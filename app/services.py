import hashlib
import ipaddress
import socket
from urllib.parse import urlparse

import httpx
from bs4 import BeautifulSoup

from .config import settings


def validate_public_url(url: str):
    parsed = urlparse(url)

    if parsed.scheme not in ("http", "https") or not parsed.hostname:
        raise ValueError("Chi chap nhan URL HTTP/HTTPS hop le.")

    host = parsed.hostname.lower()

    if host in {"localhost", "localhost.localdomain"} or host.endswith(".local"):
        raise ValueError("Khong cho phep truy cap hostname local.")

    try:
        infos = socket.getaddrinfo(
            host,
            parsed.port or (443 if parsed.scheme == "https" else 80),
            type=socket.SOCK_STREAM,
        )
        addresses = {
            ipaddress.ip_address(info[4][0].split("%")[0])
            for info in infos
        }

        if not addresses or any(not addr.is_global for addr in addresses):
            raise ValueError("URL tro den IP private, loopback hoac reserved.")

    except socket.gaierror as exc:
        raise ValueError(f"Khong phan giai duoc hostname: {exc}") from exc


async def search_web(query: str, limit: int = 8):
    endpoint = settings.searxng_url.rstrip("/") + "/search"

    async with httpx.AsyncClient(
        timeout=20,
        follow_redirects=False,
        trust_env=False,
    ) as client:
        response = await client.get(
            endpoint,
            params={
                "q": query,
                "format": "json",
                "language": "all",
            },
        )
        response.raise_for_status()
        payload = response.json()

    results = []

    for item in payload.get("results", [])[:min(max(limit, 1), 20)]:
        url = item.get("url", "")

        if url.startswith(("https://", "http://")):
            results.append({
                "title": str(item.get("title", ""))[:500],
                "url": url[:2000],
                "content": str(item.get("content", ""))[:1500],
            })

    return results


async def fetch_page(url: str):
    validate_public_url(url)

    headers = {
        "User-Agent": "MitreCloneKnowledgeAssistant/1.0"
    }

    async with httpx.AsyncClient(
        timeout=settings.fetch_timeout_seconds,
        follow_redirects=False,
        trust_env=False,
    ) as client:
        async with client.stream("GET", url, headers=headers) as response:
            if response.status_code >= 300:
                raise ValueError(
                    f"HTTP {response.status_code}; redirects are disabled."
                )

            content_type = response.headers.get(
                "content-type", ""
            ).lower()

            if not any(t in content_type for t in (
                "text/html", "text/plain", "application/xhtml"
            )):
                raise ValueError(
                    f"Khong ho tro content type: {content_type}"
                )

            body = bytearray()

            async for chunk in response.aiter_bytes():
                body.extend(chunk)

                if len(body) > settings.max_fetch_bytes:
                    raise ValueError("Trang web vuot gioi han kich thuoc.")

    html = bytes(body).decode("utf-8", errors="replace")
    soup = BeautifulSoup(html, "html.parser")

    for node in soup([
        "script", "style", "nav", "footer",
        "header", "noscript", "svg", "iframe"
    ]):
        node.decompose()

    title = soup.title.get_text(" ", strip=True) if soup.title else url
    content = " ".join(soup.get_text(" ", strip=True).split())
    content = content[:50000]

    if len(content) < 80:
        raise ValueError("Khong trich xuat duoc noi dung co ich.")

    digest = hashlib.sha256(content.encode("utf-8")).hexdigest()

    return title[:500], content, digest


async def ollama_embed(text: str):
    async with httpx.AsyncClient(
        timeout=120,
        trust_env=False,
    ) as client:
        response = await client.post(
            settings.ollama_url.rstrip("/") + "/api/embed",
            json={
                "model": settings.embed_model,
                "input": text[:12000],
            },
        )
        response.raise_for_status()
        data = response.json()

    embeddings = data.get("embeddings") or []

    if not embeddings:
        raise RuntimeError("Ollama khong tra ve embedding.")

    return embeddings[0]


async def ollama_generate(prompt: str):
    async with httpx.AsyncClient(
        timeout=240,
        trust_env=False,
    ) as client:
        response = await client.post(
            settings.ollama_url.rstrip("/") + "/api/generate",
            json={
                "model": settings.chat_model,
                "prompt": prompt,
                "stream": False,
                "options": {"temperature": 0.2},
            },
        )
        response.raise_for_status()
        data = response.json()

    return data.get("response", "").strip()