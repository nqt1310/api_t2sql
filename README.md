# Start postgre vì m đi làm mà 
sudo systemctl restart postgresql

# Bật venv

cd meta_rag/
source .venv/bin/activate
cd ..
cd api_t2sql/

# Setup cho Mistral (lần đầu)

cp .env.mistral .env
# Edit .env và điền database credentials
ollama pull mistral-nemo:latest

# Run API

python main_mcp.py

# Access Frontend (mặc định bật)
# Mở browser: http://localhost:8000

# Tắt frontend (chỉ dùng API)
# Thêm vào .env: ENABLE_FRONTEND=false

# Run Test Cases

python test_cases.py

# Check Model Performance

python check_model.py

# Quick Fix for Mistral

python quick_fix.py

# Get Model Recommendations

python model_optimizer.py mistral-nemo:latest

Checklist Tasks:

- Sửa nốt câu lệnh query + Tạo bảng trên postgres: Chưa xong
- Cân nhắc việc lưu model kiểu khác (chưa nghĩ ra lắm hehe, để thử cache nó luôn)
- Ask GPT for kiểu con này có thể tích hợp thêm 1 task nữa đc k 

## Mistral Tips:

- **Temperature phải thấp**: 0.1 là tối ưu (không cao hơn 0.2)
- **Model tốt nhất**: mistral-nemo:latest
- **Nếu vẫn lỗi JSON**: Chạy `python quick_fix.py` để tự động fix
- **Test model**: `python check_model.py` để kiểm tra xem Mistral có hoạt động tốt không 




curl -X POST http://localhost:8000/agent/query \
  -H "Content-Type: application/json" \
  -d '{"query": "Lấy họ tên khách hàng có số giấy tờ định danh cá nhân = 001201015338", "execute": false}'

  

  
curl -X POST http://localhost:8000/agent/query \
  -H "Content-Type: application/json" \
  -d '{"query": "Cho tôi thông tin khách hàng bao gồm tên đầy đủ, mã số thuế cá nhân, giới tính, địa chỉ đầy đủ, số điện thoại có căn cước sau: 12366;156345;6325489;365412;3164623…", "execute": false}'

  