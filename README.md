## Install Dependencies

```bash
pip install -r requirements.txt
```

## Run the FastAPI server

```bash
uvicorn main:app --reload
```

The API is available at [http://localhost:8000][https://chatbot-backend-levg.onrender.com/].


## 🧩 API Endpoints

- `POST /api/chat`  
  Send a message, get a bot response.  
  **Body:** `{ "message": "hi", "session_id": "..." }`  
  **Returns:** `{ response, session_id, message_type, is_complete }`

- `POST /api/reset-session`  
  Reset a session.  
  **Body:** `{ "session_id": "..." }`

- `GET /api/session/{session_id}`  
  Get session info (history, state, etc).
---