# Trợ lý tri thức Qwen + SearXNG

Ứng dụng FastAPI cung cấp giao diện tiếng Việt để hỏi Qwen, tìm kiếm bằng
SearXNG, nạp URL và cập nhật kho tri thức RAG. FastAPI, SearXNG và Valkey
chạy trong Docker Compose; ứng dụng kết nối tới Ollama đang chạy trên máy
Windows. Chỉ giao diện được mở trên máy ở
`http://localhost:8081`.

## Khởi chạy

Yêu cầu Docker Desktop và Docker Compose. Nếu chưa có `.env`, tạo khóa ngẫu
nhiên trong PowerShell:

```powershell
$bytes = New-Object byte[] 32
$rng = [System.Security.Cryptography.RandomNumberGenerator]::Create()
$rng.GetBytes($bytes)
$rng.Dispose()
$secret = -join ($bytes | ForEach-Object { $_.ToString("x2") })
"SEARXNG_SECRET=$secret" | Set-Content -Encoding ascii .env
```

Giá trị `SEARXNG_SECRET` trong `.env` phải khớp với `server.secret_key` trong
`config/settings.yml`. Không commit hoặc chia sẻ `.env`.

Từ thư mục dự án trong PowerShell:

```powershell
docker compose config -q
docker compose up -d --build
docker compose ps
```

Đảm bảo Ollama trên Windows đang chạy và đã có các model ứng dụng sử dụng.
Nếu thiếu model, tải chúng bằng PowerShell:

```powershell
ollama pull qwen3:8b
ollama pull nomic-embed-text
```

Mở `http://localhost:8081`. FastAPI kết nối tới Ollama qua
`host.docker.internal:11434`, giữ nguyên Ollama và các model đã cài trên máy.

## Sử dụng giao diện

- **Trạng thái dịch vụ:** kiểm tra kết nối tới FastAPI, SearXNG, Ollama và kho
  vector. Danh sách model hiện trong Ollama giúp xác nhận Qwen đã được tải.
- **Hỏi đáp tri thức:** nhập câu hỏi; có thể bật tìm kiếm web để kết hợp nguồn
  SearXNG với tài liệu đã nạp.
- **Nạp URL:** tải một trang web công khai, tóm tắt bằng Qwen, tạo embedding và
  lưu vào kho RAG.
- **Cập nhật từ SearXNG:** nhập một chủ đề trên mỗi dòng; để trống để dùng các
  chủ đề mặc định. Kết quả tìm kiếm được thu thập và thêm vào kho tri thức.
- **Tài liệu trong kho:** xem tài liệu đã nạp, tóm tắt và thời gian cập nhật.

## Cấu hình

Có thể đặt các biến sau trong `.env` để thay đổi mặc định:

```dotenv
CHAT_MODEL=qwen3:8b
EMBED_MODEL=nomic-embed-text
UPDATE_QUERIES=AI research news;Python release notes;cybersecurity news
```

`UPDATE_QUERIES` phân cách các chủ đề mặc định bằng dấu chấm phẩy. Có thể đổi
model bằng tên model Ollama khác, nhưng cần tải model đó trước. Sau khi đổi
cấu hình, áp dụng bằng `docker compose up -d`.

Ứng dụng kết nối SearXNG và Ollama qua tên dịch vụ nội bộ `searxng` và
`host.docker.internal`. SearXNG chỉ dùng cổng nội bộ Docker 8080; giao diện
FastAPI dùng cổng máy chủ 8081. Dữ liệu SQLite, Chroma và log được lưu trong
`knowledge/` và `logs/`; model Ollama tiếp tục được lưu bởi cài đặt Ollama
trên máy.

## API

- `GET /api/health` — trạng thái dịch vụ và số đoạn trong kho vector.
- `POST /api/search` — tìm kiếm web.
- `POST /api/ingest/url` — nạp một URL.
- `POST /api/update` — tìm và nạp nội dung theo chủ đề.
- `POST /api/ask` — hỏi đáp RAG, tùy chọn kết hợp tìm kiếm web.
- `GET /api/documents` — danh sách tài liệu và thống kê.

Ví dụ cập nhật tri thức:

```powershell
Invoke-RestMethod `
  -Uri "http://localhost:8081/api/update" `
  -Method Post `
  -ContentType "application/json" `
  -Body '{"queries":["Qwen release news","FastAPI documentation"],"results_per_query":3}'
```

## Vận hành và xử lý sự cố

```powershell
docker compose logs --tail=100 app
docker compose logs --tail=100 searxng
docker compose logs --tail=100 ollama
docker compose restart app
```

- Nếu giao diện không mở được, kiểm tra cổng 8081 có bị ứng dụng khác sử dụng
  không và xem `docker compose ps`.
- Nếu trạng thái Ollama báo lỗi, xác nhận Ollama trên Windows đang chạy và
  Docker có thể kết nối tới `host.docker.internal:11434`. Nếu model chưa có,
  chạy hai lệnh `ollama pull` ở phần khởi chạy.
- Nếu SearXNG báo lỗi, xác nhận `SEARXNG_SECRET` khớp với
  `server.secret_key` và xem log container.
- `docker compose down` dừng và xóa container nhưng giữ dữ liệu trong thư mục
  dự án; model Ollama vẫn nằm trong cài đặt trên máy.
