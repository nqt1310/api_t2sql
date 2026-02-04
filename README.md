# Start postgre vì m đi làm mà 
sudo systemctl restart postgresql

# Bật venv

cd meta_rag/
source .venv/bin/activate
cd ..
cd api_t2sql/dea

# Run API

python main_mcp.py

Checklist Tasks:

- Sửa nốt câu lệnh query + Tạo bảng trên postgres: Chưa xong
- Cân nhắc việc lưu model kiểu khác (chưa nghĩ ra lắm hehe, để thử cache nó luôn)
- Ask GPT for kiểu con này có thể tích hợp thêm 1 task nữa đc k 




curl -X POST http://localhost:8000/agent/query \
  -H "Content-Type: application/json" \
  -d '{"query": "Lấy danh sách khách hàng có số giấy tờ định danh cá nhân = 001201015338", "execute": false}'

  