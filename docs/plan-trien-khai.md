# Plan triển khai Web thiên văn

Bài cuối kì, làm cá nhân. Hạn nộp: **thứ 4, 11/11/2026**, còn 7 ngày tính từ 4/11.

**Trạng thái: đã duyệt và đã làm xong toàn bộ F01-F14 ngày 4/11/2026, hiện có 39 thiên thể và 39 bài. Số liệu đang là bản dự phòng vì chưa có khoá API; bài viết là bản nháp cần đọc lại.**

**Việc còn lại:**
- Đọc lại và sửa 39 bài nháp, đối chiếu số liệu với nguồn.
- Hỏi giảng viên có cần báo cáo hay vấn đáp không.
- Lấy khoá API nếu muốn số liệu từ API, kiểm tra giấy phép ảnh.
- Thử trên điện thoại thật. Sao lưu thư mục dự án vì chưa dùng Git.
- Chưa làm: bàn phím và trình đọc màn hình, sắp xếp lại trang Khám phá, tìm kiếm theo tiêu đề bài, trang lỗi 403/404 riêng.
- Chưa chốt: đưa tên "Xóm Mặt Trời" lại header trang chủ không, luật tính điểm ở trang So sánh.

## Mặc định mình đã chọn (bạn sửa được)

| Mục | Lựa chọn | Lý do |
|---|---|---|
| Django | 5.2 LTS, cài trong venv | Máy đang có 4.2.16 trên Python 3.13, nhưng bản 4.2 không hỗ trợ chính thức Python 3.13 |
| Cơ sở dữ liệu | SQLite | Chỉ chạy local, không cần cài thêm gì |
| Frontend | Bootstrap 5 + CSS riêng + JS thuần | Form ghi cả JS thuần và Bootstrap, nên dùng cả hai |
| Thư viện JS | Bootstrap, Three.js, Chart.js lưu trong `static/vendor/` | Lúc demo không có mạng vẫn chạy |
| Cấu trúc | Project `config`, một app `thienvan` | Một app là đủ cho phạm vi này |
| Hành tinh | 8 hành tinh, không có Sao Diêm Vương | Sao Diêm Vương không còn được xếp là hành tinh |
| Đánh giá | chấm theo đánh giá 1 sao, 2 sao,... và sửa được | ko vì lí do gì, đánh giá bài viết vẫn  phải sửa được|
| Chặn người dùng | Bỏ tick `is_active` trong Django admin | Có sẵn: tài khoản bị chặn không đăng nhập được và mất phiên đang mở |

## Phong cách giao diện

Tối như vũ trụ nhưng vui tươi, không nghiêm túc như web của NASA. NASA chỉ để tham khảo cách xếp thông tin ở trang chi tiết.

- **Màu:** nền tím than rất tối, chữ sáng, cam là màu nhấn chính, thêm một hai màu tươi phụ cho nhãn và hộp "có thể bạn chưa biết".
- **Hình khối:** bo góc lớn, thẻ thiên thể nổi nhẹ và nhúc nhích khi rê chuột. Hiệu ứng tắt theo `prefers-reduced-motion`.
- **Chữ:** font tròn trịa cho tiêu đề, có đủ dấu tiếng Việt, lưu trong `static/vendor/`. Nội dung bài dùng font dễ đọc.
- **Giọng văn:** bài viết và các thông báo thân thiện, ví dụ khi tìm không ra thì "Chưa thấy thiên thể này trong vũ trụ của mình". Số liệu vẫn phải chính xác.

## Bước 1: Danh sách chức năng

Làm theo thứ tự từ trên xuống.

| Mã | Chức năng | Nhóm | Trường hợp biên | Phụ thuộc |
|---|---|---|---|---|
| F01 | Models và admin | Bắt buộc | Không xoá được hành tinh còn vệ tinh | |
| F02 | Lệnh `nap_du_lieu` lấy số liệu từ API | Bắt buộc | Chạy lại không tạo trùng, không ghi đè bài viết; API lỗi hoặc thiếu trường | F01 |
| F03 | Danh sách thiên thể, lọc theo loại và hành tinh mẹ | Bắt buộc | Tham số lọc sai; không có kết quả | F01 |
| F04 | Trang chi tiết: số liệu, bài viết, vệ tinh, "có thể bạn chưa biết" | Bắt buộc | Số liệu rỗng hiện "Chưa có"; Sao Thuỷ, Sao Kim không có vệ tinh; chưa có bài viết | F01 |
| F05 | Đăng ký, đăng nhập, đăng xuất bằng số điện thoại hoặc Gmail, không dùng username | Bắt buộc | Trùng số điện thoại hoặc Gmail; sai định dạng; `+84...` và `0...` là cùng một số; Gmail viết hoa và viết thường là cùng một địa chỉ; tài khoản bị chặn | |
| F06 | Tìm kiếm và gợi ý AJAX | Bắt buộc | "mat trang", "MẶT TRĂNG", "Sao Hỏa" và "Sao Hoả" đều phải ra kết quả; ô tìm rỗng | F04 |
| F07 | Chấm sao 1-5, điểm trung bình | Bắt buộc | Chấm lại thì cập nhật số sao cũ, không tạo thêm lượt; số sao ngoài 1-5; chưa đăng nhập; chưa ai chấm | F04, F05 |
| F08 | Lưu yêu thích, danh sách đã lưu | Bắt buộc | Bấm lưu 2 lần; chưa đăng nhập | F04, F05 |
| F09 | Xem hành tinh 3D | Nên có | Trình duyệt không có WebGL thì hiện ảnh tĩnh; texture lỗi | F04 |
| F10 | So sánh 2 thiên thể | Nên có | Chọn trùng; thiếu số liệu; chênh lệch quá lớn | F04 |
| F11 | Khí quyển, mây, vành đai Sao Thổ | Dư thời gian | | F09 |
| F12 | Tính cân nặng trên các hành tinh | Dư thời gian | Nhập số âm hoặc không phải số; thiếu trọng lực | F04 |
| F14 | Admin thêm bài viết ngay trên web: vào thiên thể có sẵn, hoặc thêm hành tinh mới (beta) | Thêm sau khi duyệt | Người thường bị từ chối; trùng tên; tên không tạo được đường dẫn; số không hợp lệ | F01, F04 |
| F13 | Mặt Trời: loại "Ngôi sao", trang chi tiết và bài viết, bấm được từ trang chủ; đổi tên web thành Xóm Mặt Trời | Thêm sau khi duyệt | Không có hành tinh mẹ; database chưa có Mặt Trời thì trang chủ vẫn mở được | F04 |

## Bước 2: Thiết kế dữ liệu

**`ThienThe`**
- Định danh: `ten`, `ten_en`, `ten_khong_dau`, `slug`, `api_id` (unique)
- Phân loại: `loai` (hành tinh / vệ tinh), `hanh_tinh_me`
- Số liệu, đều cho phép rỗng: `ban_kinh_km`, `khoi_luong_kg`, `trong_luc`, `chu_ky_quy_dao_ngay`, `chu_ky_tu_quay_gio`, `nhiet_do_tb_k`

**`BaiViet`**: `thien_the`, `tieu_de`, `noi_dung`, `co_the_ban_chua_biet` (1-2 câu giọng vui, hiện thành một hộp nhỏ ngay dưới bài viết chính; cho phép rỗng, rỗng thì ẩn hộp), `ngay_dang`

**Tài khoản**: dùng `User` có sẵn của Django, không cần model riêng. Số điện thoại hoặc Gmail được chuẩn hoá rồi lưu vào cột `username`, nên cột này tự chặn trùng và người dùng không phải đặt username.

**`DanhGia`**: `nguoi_dung`, `bai_viet`, `so_sao`. Ràng buộc: unique theo (`nguoi_dung`, `bai_viet`) và `so_sao` từ 1 đến 5.

**`YeuThich`**: `nguoi_dung`, `bai_viet`, `ngay_luu`. Ràng buộc: unique theo (`nguoi_dung`, `bai_viet`).

Quan hệ:

```text
ThienThe (hành tinh) 1 ── 0..n ThienThe (vệ tinh)   hanh_tinh_me: FK tự tham chiếu, PROTECT
ThienThe             1 ── 0..n BaiViet              FK; bài cũ nhất là bài chính
User, BaiViet        1 ── 0..n DanhGia, YeuThich    FK, CASCADE
```

Các quyết định chính:
- Bài viết tách khỏi thiên thể, nên chạy lại lệnh API không thể đụng vào bài bạn tự viết.
- Ràng buộc đặt trong database: hành tinh không có hành tinh mẹ, vệ tinh bắt buộc có.
- Điểm trung bình tính bằng `Avg`, không lưu thành cột riêng, nên không bị lệch.
- `ten_khong_dau` được tạo tự động khi lưu (bỏ dấu, `đ` thành `d`). Tìm kiếm so với cột này vì `icontains` của SQLite chỉ không phân biệt hoa thường với ký tự ASCII.

**Lệnh `nap_du_lieu`:**
- Đọc khoá từ biến môi trường `SOLAR_API_KEY`, không ghi khoá vào code.
- Lấy danh sách 38 thiên thể và tên tiếng Việt từ `data/danh_sach.json`.
- Dùng `update_or_create` theo `api_id` và chỉ ghi các cột số liệu.
- Xuất kết quả ra `data/thien_the.json`. Máy chấm chỉ cần `loaddata`, không cần API, khoá hay mạng.

**30 vệ tinh đề xuất:**

| Hành tinh | Vệ tinh |
|---|---|
| Trái Đất | Mặt Trăng |
| Sao Hoả | Phobos, Deimos |
| Sao Mộc | Io, Europa, Ganymede, Callisto, Amalthea, Himalia |
| Sao Thổ | Titan, Enceladus, Mimas, Tethys, Dione, Rhea, Iapetus, Hyperion, Phoebe, Janus, Pandora |
| Sao Thiên Vương | Miranda, Ariel, Umbriel, Titania, Oberon, Puck |
| Sao Hải Vương | Triton, Proteus, Nereid, Larissa |

**Sơ đồ:** chỉ vẽ ERD trên vì đề không yêu cầu báo cáo. Nếu giảng viên yêu cầu báo cáo thì vẽ thêm bằng draw.io.

## Bước 3: Setup

1. Tạo venv, cài Django 5.2 (đã xong), tạo project và app.
2. Viết `requirements.txt` và `README.md` với các lệnh cài và chạy.
3. Chưa dùng Git và GitHub, khi nào bạn yêu cầu thì làm.

## Bước 4: Kiểm thử

Dùng `django.test` có sẵn, chạy bằng `python manage.py test`. Không cài thêm thư viện.

- **Có test tự động:** F02, F05 (tài khoản bị chặn), F06, F07, F08 và các ràng buộc model.
- **Xem bằng mắt:** giao diện, 3D, biểu đồ, hiển thị trên điện thoại.

## Bước 5: Lịch làm và đầu ra từng ngày

| Ngày | Làm | Đầu ra kiểm tra được |
|---|---|---|
| T4 4/11 | Duyệt plan, lấy khoá API, setup, F01, F02 | 38 thiên thể trong admin; chạy lệnh 2 lần vẫn là 38 |
| T5 5/11 | Layout tối, F03, F04 | Lọc được; mở được trang chi tiết Sao Mộc và Sao Kim |
| T6 6/11 | F05, F06 | Gõ "mat trang" thấy gợi ý; tài khoản bị chặn không đăng nhập được |
| T7 7/11 | F07, F08, bài viết 8 hành tinh | **Xong toàn bộ phần bắt buộc**, test xanh |
| CN 8/11 | F09 | Xoay được 8 hành tinh 3D |
| T2 9/11 | F10, bài viết 30 vệ tinh | So sánh được 2 thiên thể; đủ 38 bài |
| T3 10/11 | Ngừng thêm chức năng; sửa lỗi, kiểm tra điện thoại, F11 và F12 nếu còn giờ | Chạy được từ bản sao sạch |
| T4 11/11 | Nộp bài | |

**Quy tắc cắt:** nếu đến hết 7/11 chưa xong phần bắt buộc, cắt theo thứ tự F12, F11, F10, F09.

**Vòng lặp cho mỗi chức năng:** viết test cho các trường hợp biên → viết code → chạy toàn bộ test → đọc lại code đến khi tự giải thích được.

## Bước 6: Chuẩn bị nộp

1. Xuất dữ liệu kèm bài viết ra `data/thien_the.json`.
2. Sao chép dự án sang thư mục mới, bỏ `.venv/` và `db.sqlite3`, rồi chạy:

   ```powershell
   python -m venv .venv
   .venv\Scripts\pip install -r requirements.txt
   .venv\Scripts\python manage.py migrate
   .venv\Scripts\python manage.py loaddata data/thien_the.json
   .venv\Scripts\python manage.py test
   .venv\Scripts\python manage.py runserver
   ```

3. Tạo tài khoản admin và demo một lượt: khách → người dùng → admin chặn người dùng.
4. Ghi nguồn texture và nguồn số liệu ở chân trang và trong README.

## Rủi ro

| Rủi ro | Tình trạng | Cách xử lý |
|---|---|---|
| API cần khoá | Đã gọi thử api.le-systeme-solaire.net không có khoá: lỗi 401. Chưa xem được dữ liệu thật | Lấy khoá và kiểm tra ngay trong ngày 4/11. Nếu không lấy được thì nhập tay số liệu vào JSON từ bảng số liệu của NASA |
| Đăng ký không xác thực | Không gửi SMS hay email xác nhận, nên ai cũng có thể đăng ký bằng số hoặc Gmail của người khác | Chấp nhận với bài chạy local; không hiển thị số điện thoại hoặc Gmail ở trang công khai |
| Thiếu số liệu vệ tinh nhỏ | Dự đoán, chưa kiểm tra | Cho phép rỗng, hiện "Chưa có" |
| Viết 38 bài tốn thời gian nhất | Khoảng 6.000 từ: 8 hành tinh ~350 từ, 30 vệ tinh ~100 từ | Viết rải theo ngày, vệ tinh viết ngắn; "có thể bạn chưa biết" làm cho 8 hành tinh trước, vệ tinh nếu còn giờ |
| Không có Git | Không có lịch sử để quay lại hay bản sao dự phòng nếu sửa hỏng hoặc mất máy | Cuối mỗi ngày sao chép dự án sang nơi khác, bỏ `.venv/` |
| Texture 3D | Chưa kiểm tra giấy phép và việc có đủ bump map không | Kiểm tra khi làm F09; dùng bản 2K cho nhẹ; hành tinh khí không cần bump map |
| Biểu đồ so sánh | Khối lượng Sao Mộc lớn hơn vệ tinh nhỏ rất nhiều lần | Mỗi chỉ số một biểu đồ, dùng trục logarit |

## Không làm

Quên mật khẩu, xác thực email, bình luận, deploy online, nút bật tắt dark mode, 3D cho vệ tinh, phân trang (chỉ có 38 thiên thể).
