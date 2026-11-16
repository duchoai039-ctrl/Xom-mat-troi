# Xóm Mặt Trời

Website giới thiệu Mặt Trời, 8 hành tinh và 30 vệ tinh trong hệ Mặt Trời, làm bằng Django. Bài cuối kì.

## Cài và chạy (Windows)

```powershell
python -m venv .venv
.venv\Scripts\pip install -r requirements.txt
.venv\Scripts\python manage.py migrate
.venv\Scripts\python manage.py loaddata data/thien_the.json
.venv\Scripts\python manage.py createsuperuser
.venv\Scripts\python manage.py runserver
```

Mở http://127.0.0.1:8000/. Trang quản trị ở http://127.0.0.1:8000/admin/. Muốn chặn người dùng, bỏ tick "Có hiệu lực" (`is_active`) của họ trong mục Người dùng.

Chạy test:

```powershell
.venv\Scripts\python manage.py test
```

## Cập nhật số liệu từ API

Web chỉ đọc database, không gọi API khi có người truy cập. Lệnh sau chỉ cập nhật những số lấy được từ API, không đụng vào tên, màu và bài viết:

```powershell
$env:SOLAR_API_KEY = "khoá của bạn"
.venv\Scripts\python manage.py nap_du_lieu
```

Không có khoá thì thiên thể chưa có trong database dùng số liệu dự phòng trong `data/danh_sach.json`, còn thiên thể đã có giữ nguyên. Sau khi cập nhật, xuất lại dữ liệu để bản nộp có số mới:

```powershell
.venv\Scripts\python -Xutf8 manage.py dumpdata thienvan.ThienThe thienvan.BaiViet --indent 2 -o data/thien_the.json
```

## Đưa lên mạng (Render + Neon, miễn phí)

| Phần | Dịch vụ | Ghi chú |
|---|---|---|
| Chạy web | Render, gói Free | Ngủ sau 15 phút không ai vào; lần đầu vào lại chờ khoảng 1 phút |
| Database PostgreSQL | Neon, gói Free | Ổ đĩa Render bị xoá mỗi lần deploy, nên dữ liệu không thể để ở SQLite |

Ảnh hành tinh, font, CSS và JS nằm sẵn trong code, WhiteNoise phục vụ, nên không cần Cloudinary. Trên máy, web vẫn chạy như cũ với SQLite; chỉ khi có biến `DATABASE_URL` mới dùng Neon.

> Chuỗi kết nối Neon là mật khẩu. Chỉ dán vào trang Render hoặc cửa sổ PowerShell trên máy mình, không đưa vào code, GitHub hay chat.

**1. Neon.** Đăng nhập https://console.neon.tech, tạo project `xom-mat-troi` ở vùng AWS Asia Pacific (Singapore). Mở **Connect**, tắt **Connection pooling**, copy chuỗi `postgresql://...neon.tech/neondb?sslmode=require`.

**2. Nạp dữ liệu lên Neon, làm một lần, trước khi gửi link cho người khác.** Trong PowerShell ở thư mục dự án:

```powershell
# Xuất 39 thiên thể và bài viết từ SQLite (lấy bản mới nhất, kể cả bài đã sửa trong admin)
.venv\Scripts\python -Xutf8 manage.py dumpdata thienvan.ThienThe thienvan.BaiViet --indent 2 -o data/thien_the.json

# Trỏ tạm cửa sổ này tới Neon (chỉ có hiệu lực trong cửa sổ này)
$env:DATABASE_URL = "<dán chuỗi Neon>"
.venv\Scripts\python manage.py migrate
.venv\Scripts\python -Xutf8 manage.py loaddata data/thien_the.json

# Tài khoản quản trị trên mạng: mật khẩu mạnh, không dùng 12345
.venv\Scripts\python manage.py createsuperuser
```

Xong thì đóng cửa sổ PowerShell này để bỏ biến `DATABASE_URL`.

**3. Render.** Đẩy code lên GitHub, rồi đăng nhập https://dashboard.render.com bằng GitHub → **New → Blueprint** → chọn repo. Render đọc `render.yaml` và tạo dịch vụ `xom-mat-troi` (vùng Singapore, gói Free). Dán chuỗi Neon vào `DATABASE_URL`; `DJANGO_SECRET_KEY` Render tự tạo. Bấm **Apply**, Render chạy `build.sh` rồi cho link dạng `https://xom-mat-troi.onrender.com`.

**Sau khi deploy:** đẩy code lên nhánh `main` là Render tự deploy lại. Xem lỗi ở Render → dịch vụ → **Logs**; cần trang lỗi chi tiết thì tạm đặt biến `DJANGO_DEBUG=1`, xem xong xoá ngay.

## Nguồn

- Ảnh bề mặt hành tinh: [Solar System Scope](https://www.solarsystemscope.com/textures/)
- Ảnh phi hành gia Bruce McCandless, 1984: NASA, lấy qua Unsplash
- Số liệu: NASA và [Solar System OpenData](https://api.le-systeme-solaire.net/), có làm tròn
- Thư viện: Django, Bootstrap, Three.js, Chart.js; font Baloo 2, Be Vietnam Pro và Fredoka
