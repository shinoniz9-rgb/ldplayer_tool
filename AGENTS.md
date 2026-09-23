# Quy Tắc & Hướng Dẫn Dự Án (Project Rules)

## 1. Đồng bộ với Giao Diện Web (`web_server.py`)
- **Bắt buộc kiểm tra**: Mỗi khi có thay đổi ảnh hưởng đến tính năng, cấu hình, giao diện, nút bấm, ô chọn (combobox/option menu), ô tích (checkbox/switch) hay API điều khiển, **PHẢI luôn đồng bộ tương ứng sang `web_server.py`**.
- **Thông báo rõ ràng**: Đối với các thay đổi thuần logic xử lý ngầm (như thời gian hoãn sleep, tọa độ click nội bộ, thuật toán...) không tác động đến giao diện/API Web, không cần sửa `web_server.py`, nhưng **bắt buộc phải thông báo rõ cho người dùng**: *"Những thay đổi này thuộc logic nội bộ, không ảnh hưởng đến giao diện Web."*

## 2. Đồng bộ Thư mục Đóng Gói (`dist/`)
- Mọi thay đổi về file tài nguyên (hình ảnh trong `assets/`, cấu hình trong `config.json`) phải được sao chép/đồng bộ sang thư mục `dist/`.
- Khi có thay đổi mã nguồn cốt lõi (`main.py`, `web_server.py`), thực hiện build lại file chạy `dist/TS_Origin_Control.exe` (qua `python build_exe.py`) để đảm bảo người dùng chạy file `.exe` luôn có bản cập nhật mới nhất.

## 3. Tuyệt Đối Không Can Thiệp Vào Bản Hoạt Động (`C:\LDPlayer\dist`)
- Khi đóng gói file `.exe` hoặc làm việc, **chỉ xuất và xử lý trong phạm vi thư mục của project (`dist/` và `dist_share/`)**.
- **Tuyệt đối không tự ý sao chép, đồng bộ hay ghi đè** sang thư mục Bản hoạt động (ví dụ `C:\LDPlayer\dist` hoặc các thư mục bên ngoài). Việc cập nhật vào bản hoạt động người dùng sẽ tự mình thay thế vào sau khi kiểm tra xong.

## 4. Các Thành Phần Tuyệt Đối KHÔNG Đưa Lên Giao Diện Web (`web_server.py`)
Khi đồng bộ giao diện hoặc cập nhật từ `main.py` sang `web_server.py`, **TUYỆT ĐỐI KHÔNG ĐỒNG BỘ LẠI** các thành phần sau:
1. **Hàng Truy Kích (Card F - Cấu Hình Chiến Đấu)**: Loại bỏ hoàn toàn toàn bộ hàng này trên Web UI (gồm ô tích/nút Truy Kích, nhãn Tắt Rút Gọn, menu chọn Quái). Không sử dụng trên Web.
2. **Nút Chụp Hình (`📸`) và Nút Xóa (`✕`) ở Hàng Mời Đội (Card E - Quản Lý Tổ Đội)**: Không đưa 2 nút này lên Web UI. Hàng 1 Card E chỉ hiển thị: `[x] Mời Đội` - `Menu Số Lượng (48px)` - `Menu Map (dãn 1fr)` để đảm bảo giao diện cân đối, gọn gàng.

