# 🎨 Text-to-SQL Frontend

Frontend nhẹ cho API Text-to-SQL, được build bằng HTML/CSS/JavaScript thuần.

## 🚀 Cách sử dụng

### Option 1: Serve từ API (Recommended)
```bash
# Đảm bảo ENABLE_FRONTEND=true trong .env (mặc định)
python main_mcp.py

# Mở browser
http://localhost:8000
```

### Option 2: Mở trực tiếp file HTML
```bash
# Chỉ cần mở file trong browser
# Hoặc dùng Live Server trong VS Code
```

## ⚙️ Cấu hình

### Bật/Tắt Frontend
Trong file `.env`:
```bash
# Bật frontend (mặc định)
ENABLE_FRONTEND=true

# Tắt frontend (chỉ API)
ENABLE_FRONTEND=false
```

### CORS
API đã được cấu hình CORS để accept requests từ mọi origin. Trong production, nên giới hạn:
```python
allow_origins=["http://localhost:3000", "https://yourdomain.com"]
```

## ✨ Tính năng

- ✅ Nhập câu hỏi bằng tiếng Việt
- ✅ Toggle execute query on/off
- ✅ Hiển thị SQL query generated
- ✅ Hiển thị kết quả dạng bảng
- ✅ Copy SQL query 1 click
- ✅ API health check tự động
- ✅ Ví dụ câu hỏi mẫu
- ✅ Responsive design

## 📁 Cấu trúc

```
frontend/
├── index.html    # Giao diện chính
├── style.css     # Styles
├── script.js     # Logic xử lý
└── README.md     # File này
```

## 🛠️ Troubleshooting

### CORS Error
Nếu gặp lỗi CORS khi mở trực tiếp file HTML:
- Dùng option 1 (serve từ API)
- Hoặc dùng Live Server extension

### API không kết nối được
Kiểm tra:
1. API đang chạy: `python main_mcp.py`
2. Port đúng: `http://localhost:8000`
3. Firewall không block port 8000

### Frontend không hiện
Kiểm tra:
1. `ENABLE_FRONTEND=true` trong `.env`
2. Folder `frontend/` tồn tại
3. Restart API sau khi thay đổi config

## 🎨 Customization

### Thay đổi màu sắc
Sửa trong `style.css`:
```css
/* Gradient chính */
background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);

/* Có thể đổi thành màu khác */
background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
```

### Thêm ví dụ câu hỏi
Sửa trong `index.html`:
```html
<div class="example-card" onclick="fillExample(this)">
    <p>Câu hỏi ví dụ của bạn</p>
</div>
```

## 📝 API Endpoints sử dụng

- `POST /agent/query` - Gửi câu hỏi
- `GET /health` - Kiểm tra API status

## 🔒 Security Notes

- Frontend hiện tại chấp nhận mọi origin (CORS: `*`)
- Trong production nên:
  - Giới hạn CORS origins
  - Thêm authentication
  - Rate limiting
  - Input validation
