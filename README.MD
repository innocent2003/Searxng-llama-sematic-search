# SearXNG Docker Compose — MITRE Clone

## 1. Thông tin triển khai

- **Thư mục dự án:** `D:\MitreClone`
- **Triển khai:** Docker Compose
- **Dịch vụ:** SearXNG và Valkey
- **Địa chỉ truy cập:** http://localhost:8080
- **Phạm vi lắng nghe:** `127.0.0.1:8080` (chỉ truy cập từ máy Windows này)
- **File Compose:** `D:\MitreClone\docker-compose.yml`
- **File biến môi trường:** `D:\MitreClone\.env`
- **File cấu hình SearXNG:** `D:\MitreClone\config\settings.yml`

> Ghi chú: Tài liệu này ghi lại cấu hình đã soạn trong hướng dẫn. Hãy chạy các lệnh kiểm tra ở phần 7 để xác nhận trạng thái thực tế trên máy.

## 2. Cấu trúc thư mục

```text
D:\MitreClone\
├── docker-compose.yml
├── .env
├── config\
│   └── settings.yml
├── cache\
└── valkey\
```

- `config\settings.yml`: cấu hình SearXNG.
- `cache\`: thư mục cache được mount vào container SearXNG.
- `valkey\`: dữ liệu Valkey.
- `.env`: chứa khóa bí mật `SEARXNG_SECRET`. Không chia sẻ file này hoặc đưa vào Git.

## 3. Docker Compose

Nội dung `D:\MitreClone\docker-compose.yml`:

```yaml
services:
  searxng:
    image: searxng/searxng:latest
    container_name: searxng
    restart: unless-stopped
    ports:
      - "127.0.0.1:8080:8080"
    environment:
      SEARXNG_SECRET: "${SEARXNG_SECRET}"
      SEARXNG_BASE_URL: "http://localhost:8080/"
      SEARXNG_VALKEY_URL: "valkey://valkey:6379/0"
    volumes:
      - ./config:/etc/searxng
      - ./cache:/var/cache/searxng
    depends_on:
      - valkey

  valkey:
    image: valkey/valkey:9-alpine
    container_name: searxng-valkey
    restart: unless-stopped
    command: valkey-server --save 60 1 --loglevel warning
    volumes:
      - ./valkey:/data
```

### Lưu ý về cấu hình bí mật

Compose truyền `SEARXNG_SECRET` từ `.env` vào container. Trong `settings.yml`, trường `server.secret_key` cũng cần được đặt thành **cùng giá trị**. Không ghi khóa bí mật thật vào tài liệu này hoặc kho mã nguồn.

## 4. Biến môi trường `.env`

File `D:\MitreClone\.env` có dạng:

```dotenv
SEARXNG_SECRET=<khóa-ngẫu-nhiên-64-ký-tự-hex>
```

Tạo hoặc tạo lại khóa bằng PowerShell (chạy tại `D:\MitreClone`):

```powershell
$bytes = New-Object byte[] 32
$rng = [System.Security.Cryptography.RandomNumberGenerator]::Create()
$rng.GetBytes($bytes)
$rng.Dispose()

$secret = -join ($bytes | ForEach-Object { $_.ToString("x2") })
"SEARXNG_SECRET=$secret" | Set-Content -Encoding ascii .env
```

**Cảnh báo:** Chỉ tạo lại khóa khi chủ động muốn đổi khóa. Sau khi đổi, hãy cập nhật `server.secret_key` trong `config\settings.yml` bằng cùng giá trị rồi khởi động lại dịch vụ.

## 5. Cấu hình SearXNG

File `D:\MitreClone\config\settings.yml`:

```yaml
use_default_settings: true

general:
  debug: false
  instance_name: "SearXNG Local"

search:
  safe_search: 0
  formats:
    - html
    - json

server:
  secret_key: "THAY_BANG_GIA_TRI_SEARXNG_SECRET"
  limiter: false
  image_proxy: true

valkey:
  url: valkey://valkey:6379/0
```

Thay `THAY_BANG_GIA_TRI_SEARXNG_SECRET` bằng giá trị `SEARXNG_SECRET` trong `.env`.

- `formats: json` bật định dạng JSON cho API tìm kiếm.
- `limiter: false` thuận tiện cho thử nghiệm local nhưng không phù hợp khi mở dịch vụ ra Internet.
- `safe_search: 0` không lọc kết quả theo chế độ Safe Search. Điều chỉnh nếu cần.
- Valkey dùng URL nội bộ Docker `valkey://valkey:6379/0`.

## 6. Cài đặt và vận hành

Mở PowerShell:

```powershell
Set-Location D:\MitreClone

# Kiểm tra cú pháp và cấu hình Compose
docker compose config

# Tải image
docker compose pull

# Tạo và khởi chạy dịch vụ
docker compose up -d

# Xem trạng thái
docker compose ps
```

### Các lệnh quản trị thường dùng

```powershell
# Xem log SearXNG
docker compose logs --tail=100 searxng

# Xem log Valkey
docker compose logs --tail=50 valkey

# Theo dõi log liên tục
docker compose logs -f

# Khởi động lại dịch vụ
docker compose restart

# Dừng dịch vụ nhưng giữ container
docker compose stop

# Khởi chạy lại
docker compose up -d

# Tải image mới và áp dụng
docker compose pull
docker compose up -d

# Xóa container/network do Compose tạo (giữ các thư mục bind mount)
docker compose down
```

Không dùng `docker compose down -v` nếu không muốn xóa các Docker volume được quản lý bởi Compose. Các thư mục bind mount `config`, `cache` và `valkey` trong dự án vẫn nằm trên ổ D.

## 7. Kiểm tra hoạt động

### 7.1 Kiểm tra Docker

```powershell
docker --version
docker compose version
docker compose ps
```

### 7.2 Kiểm tra giao diện web

Mở trình duyệt:

http://localhost:8080

### 7.3 Kiểm tra API JSON

```powershell
$response = Invoke-RestMethod `
  -Uri "http://localhost:8080/search?q=MITRE+ATT%26CK&format=json"

$response.results |
  Select-Object -First 5 title, url, content |
  Format-List
```

Nếu API trả về danh sách kết quả có tiêu đề và URL, API JSON hoạt động. Nếu bị lỗi, kiểm tra log SearXNG và `settings.yml`.

## 8. Xử lý sự cố

| Triệu chứng | Kiểm tra / xử lý |
|---|---|
| Container thoát hoặc restart liên tục | `docker compose logs --tail=100 searxng` |
| Không mở được `localhost:8080` | `docker compose ps`; kiểm tra cổng 8080 có bị ứng dụng khác chiếm không |
| API không trả JSON | Kiểm tra `search.formats` có mục `json` |
| Lỗi khóa bí mật | Xác nhận `SEARXNG_SECRET` và `server.secret_key` trùng nhau |
| Không có kết quả tìm kiếm | Kiểm tra Internet, thử truy vấn khác và xem log |
| Valkey không hoạt động | `docker compose logs --tail=100 valkey`; kiểm tra URL nội bộ |

## 9. Bảo mật và lưu ý

- Cổng web được bind vào `127.0.0.1`, không công khai trực tiếp trên mạng LAN.
- Không commit `.env` vào Git. Thêm `.env` vào `.gitignore` nếu thư mục này là kho Git.
- Không nên dùng `limiter: false` khi mở dịch vụ ra ngoài máy local.
- `latest` và `9-alpine` có thể trỏ tới image mới theo thời gian. Khi cần triển khai ổn định, cân nhắc pin phiên bản cụ thể đã kiểm thử.
- Chạy SearXNG không tự động tích hợp với Ollama hoặc OpenCode; cần cấu hình MCP/tích hợp tương thích riêng.

## 10. Checklist sau cài đặt

- [ ] `docker compose config` chạy không lỗi.
- [ ] Container `searxng` và `searxng-valkey` đang chạy.
- [ ] Mở được `http://localhost:8080`.
- [ ] API `/search?q=test&format=json` trả về JSON.
- [ ] `server.secret_key` khớp với `SEARXNG_SECRET`.
- [ ] `.env` không được đưa lên Git.
