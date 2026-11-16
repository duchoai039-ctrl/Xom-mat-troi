#!/usr/bin/env bash
# Render chạy file này mỗi lần deploy (xem render.yaml).
set -o errexit   # lỗi ở bước nào thì dừng luôn, không deploy bản hỏng

pip install -r requirements.txt

python manage.py collectstatic --no-input   # gom CSS, JS, font, ảnh hành tinh vào staticfiles/ cho WhiteNoise
python manage.py migrate --no-input         # tạo / cập nhật bảng trong database Neon
# Dữ liệu 39 thiên thể và bài viết được nạp một lần từ máy (xem README), không nạp ở đây:
# nạp lại mỗi lần deploy sẽ ghi đè bài viết đã sửa trong admin.
