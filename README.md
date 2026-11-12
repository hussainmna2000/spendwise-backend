# SpendWise AI — Flask Backend

A production-ready Python Flask backend that powers the **SpendWise AI** personal finance app, featuring a Groq-powered AI chat assistant, spending analytics, predictions, and full CRUD for transactions.

---

## Prerequisites

- **Python 3.9+**
- A free **Groq API key** → [console.groq.com](https://console.groq.com)

---

## Setup

```bash
# 1. From the backend repository root

# 2. (Optional but recommended) create a virtual environment
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS / Linux
source .venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment variables
#    Copy the template and fill in your Groq API key
copy .env.example .env       # Windows
# cp .env.example .env       # macOS / Linux

# Edit .env and replace "your_groq_api_key_here" with your real key
# GROQ_API_KEY=gsk_...

# 5. Start the server
python app.py
```

The server will be available at **http://localhost:5000**.

---

## Environment Variables

| Variable        | Description                                     | Required |
|-----------------|-------------------------------------------------|----------|
| `GROQ_API_KEY`  | Your Groq API key (get it at console.groq.com)  | ✅ Yes   |
| `GROQ_MODEL`    | Groq model ID (default: `openai/gpt-oss-120b`) | No       |
| `FLASK_ENV`     | `development` or `production`                   | No       |
| `FLASK_DEBUG`   | `1` = debug mode on, `0` = off                  | No       |
| `PORT`          | Port to listen on (default: `5000`)             | No       |
| `CORS_ORIGINS`  | Comma-separated allowed frontend origins        | No       |

> **Important:** `GROQ_API_KEY` is required for the `/api/chat` endpoint to work. Without it the endpoint returns a helpful error message. The API uses an in-memory demo dataset; data resets when the process restarts.

---

## API Endpoints

| Method   | Endpoint               | Description                                      |
|----------|------------------------|--------------------------------------------------|
| `GET`    | `/api/health`          | Health check — returns service name & version    |
| `GET`    | `/api/dashboard`       | Summary stats (total spend, budget, top category)|
| `GET`    | `/api/expenses`        | List all transactions                            |
| `POST`   | `/api/expenses`        | Add a new transaction                            |
| `PUT`    | `/api/expenses/<id>`   | Update an existing transaction by ID             |
| `DELETE` | `/api/expenses/<id>`   | Delete a transaction by ID                       |
| `GET`    | `/api/categories`      | List all expense categories                      |
| `GET`    | `/api/analytics`       | Spending analytics by category                   |
| `GET`    | `/api/predictions`     | Next-month spending predictions                  |
| `GET`    | `/api/budget`          | Budget recommendations per category              |
| `POST`   | `/api/chat`            | 🤖 AI chat (Groq / LLaMA 3.3 70B)              |

---

### `/api/chat` Request Body

```json
{
  "message": "How can I reduce my food spending?",
  "sessionId": "user-session-abc123",
  "context": {
    "totalMonthlySpend": 1130.75,
    "remainingBudget": 469.25,
    "recentTransactionCount": 10
  }
}
```

### `/api/chat` Response

```json
{
  "reply": "Your food spending of $323.35 this month...",
  "structuredData": null,
  "sessionId": "user-session-abc123"
}
```

---

## Project Structure

```
backend/
├── app.py              ← Main Flask application
├── requirements.txt    ← Python dependencies
├── .env                ← Local environment variables (not committed)
├── .env.example        ← Environment variable template
└── README.md           ← This file
```

---

## Tech Stack

| Layer        | Technology                        |
|--------------|-----------------------------------|
| Framework    | Flask 3.0 + Flask-CORS            |
| AI / LLM     | Groq API (OpenAI GPT-OSS 120B)    |
| Analytics    | pandas 2.2 + scikit-learn 1.5    |
| Config       | python-dotenv                     |
| Data store   | In-memory Python list (demo mode) |
