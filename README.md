
#### c. Run the FastAPI server

```bash
uvicorn main:app --reload
```

The API will be available at [http://localhost:8000](https://chatbot-backend-levg.onrender.com/).

---

### 3. Frontend Setup (Next.js)

```bash
npm install
npm run dev
```

The frontend will be available at [http://localhost:3000](https://vercel.com/muhammad-asifs-projects-ff63202b/chatbot/BSTJfv2j4ov1JTW8bD8ufVEBjnsW).

---

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