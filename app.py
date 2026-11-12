"""
SpendWise AI - Flask Backend
A personal finance management API with AI-powered chat capabilities.
"""

import os
import uuid
import random
import math
from pathlib import Path
from datetime import datetime, timedelta
from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv

# Always load .env from the same folder as app.py (regardless of where you run the command from)
load_dotenv(Path(__file__).parent / ".env")

app = Flask(__name__)
# Allow all origins — React frontend on any localhost port can connect
CORS(app, resources={r"/api/*": {"origins": "*"}}, supports_credentials=False)

# ---------------------------------------------------------------------------
# In-Memory Data Store
# ---------------------------------------------------------------------------

transactions = [
    {"id": "TXN-1024", "title": "Whole Foods Market Grocery",      "amount": 164.80, "category": "Food",           "date": "2026-11-10", "description": "Weekly organic groceries"},
    {"id": "TXN-1023", "title": "ConEdison Electric & Gas Utility", "amount": 215.40, "category": "Bills",          "date": "2026-11-09", "description": "Monthly utility billing"},
    {"id": "TXN-1022", "title": "Uber Commute & Airport Ride",      "amount": 68.50,  "category": "Transportation", "date": "2026-11-09", "description": "Client meeting transit"},
    {"id": "TXN-1021", "title": "Nordstrom Winter Apparel",         "amount": 342.00, "category": "Shopping",       "date": "2026-11-08", "description": "Winter coat and sweater"},
    {"id": "TXN-1020", "title": "Blue Bottle Coffee & Bistro Lunch","amount": 46.25,  "category": "Food",           "date": "2026-11-07", "description": "Team lunch meeting"},
    {"id": "TXN-1019", "title": "Coursera Machine Learning",        "amount": 79.00,  "category": "Education",      "date": "2026-11-06", "description": "Monthly certificate subscription"},
    {"id": "TXN-1018", "title": "One Medical Annual Checkup",       "amount": 145.00, "category": "Healthcare",     "date": "2026-11-06", "description": "Annual health checkup"},
    {"id": "TXN-1017", "title": "Netflix & Spotify Bundle",         "amount": 28.00,  "category": "Entertainment",  "date": "2026-11-05", "description": "Streaming subscriptions"},
    {"id": "TXN-1016", "title": "Amazon Prime Household",           "amount": 89.50,  "category": "Shopping",       "date": "2026-11-04", "description": "Home essentials and books"},
    {"id": "TXN-1015", "title": "Trader Joe's Weekly Shop",         "amount": 112.30, "category": "Food",           "date": "2026-11-03", "description": "Weekly groceries"},
]

CATEGORIES = [
    "Food", "Bills", "Transportation", "Shopping",
    "Education", "Healthcare", "Entertainment", "Other"
]

# Budget baselines per category (monthly allocation in USD)
BUDGET_BASELINES = {
    "Food":           400,
    "Bills":          300,
    "Transportation": 150,
    "Shopping":       250,
    "Education":      100,
    "Healthcare":     200,
    "Entertainment":  100,
    "Other":          100,
}

# In-memory chat session store  {sessionId: [{"role": ..., "content": ...}, ...]}
chat_sessions: dict[str, list] = {}

# ---------------------------------------------------------------------------
# Helper utilities
# ---------------------------------------------------------------------------

def generate_txn_id() -> str:
    """Generate a transaction ID like TXN-XXXX."""
    existing_ids = {transaction["id"] for transaction in transactions}
    while True:
        candidate = f"TXN-{random.randint(1000, 9999)}"
        if candidate not in existing_ids:
            return candidate


def validate_expense(data: dict, *, partial: bool = False) -> str | None:
    """Validate client supplied expense fields before mutating the store."""
    if not isinstance(data, dict):
        return "Request body must be a JSON object."
    if not partial and (not isinstance(data.get("title"), str) or not data["title"].strip()):
        return "Field 'title' is required and must be a non-empty string."
    if "title" in data and (not isinstance(data["title"], str) or not data["title"].strip()):
        return "Field 'title' must be a non-empty string."
    if not partial and "amount" not in data:
        return "Field 'amount' is required."
    if "amount" in data:
        try:
            amount = float(data["amount"])
            if not math.isfinite(amount) or amount < 0:
                raise ValueError
        except (TypeError, ValueError, OverflowError):
            return "Field 'amount' must be a finite, non-negative number."
    if "category" in data and (not isinstance(data["category"], str) or not data["category"].strip()):
        return "Field 'category' must be a non-empty string."
    if "date" in data:
        try:
            datetime.strptime(data["date"], "%Y-%m-%d")
        except (TypeError, ValueError):
            return "Field 'date' must use YYYY-MM-DD format."
    for field in ("description",):
        if field in data and not isinstance(data[field], str):
            return f"Field '{field}' must be a string."
    return None


def compute_category_totals(txn_list: list) -> dict:
    totals: dict[str, float] = {}
    for t in txn_list:
        cat = t.get("category", "Other")
        totals[cat] = round(totals.get(cat, 0) + t["amount"], 2)
    return totals


def compute_analytics(txn_list: list) -> dict:
    """Compute analytics; uses pandas if available, otherwise manual."""
    if not txn_list:
        return {
            "categoryTotals": {},
            "totalSpend": 0,
            "topCategory": None,
            "averageTransaction": 0,
            "transactionCount": 0,
        }

    try:
        import pandas as pd  # type: ignore
        df = pd.DataFrame(txn_list)
        category_totals = df.groupby("category")["amount"].sum().round(2).to_dict()
        total_spend = round(df["amount"].sum(), 2)
        top_category = max(category_totals, key=category_totals.get)
        avg_transaction = round(df["amount"].mean(), 2)
    except ImportError:
        category_totals = compute_category_totals(txn_list)
        total_spend = round(sum(t["amount"] for t in txn_list), 2)
        top_category = max(category_totals, key=category_totals.get) if category_totals else None
        avg_transaction = round(total_spend / len(txn_list), 2) if txn_list else 0

    return {
        "categoryTotals": category_totals,
        "totalSpend": total_spend,
        "topCategory": top_category,
        "averageTransaction": avg_transaction,
        "transactionCount": len(txn_list),
    }


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.route("/api/health", methods=["GET"])
def health():
    return jsonify({
        "status": "ok",
        "version": "1.0.0",
        "service": "SpendWise AI Flask Backend"
    })


@app.route("/api/dashboard", methods=["GET"])
def dashboard():
    analytics = compute_analytics(transactions)
    total = analytics["totalSpend"]
    budget_total = sum(BUDGET_BASELINES.values())
    return jsonify({
        "totalMonthlySpend": total,
        "totalBudget": budget_total,
        "remainingBudget": round(budget_total - total, 2),
        "transactionCount": analytics["transactionCount"],
        "topCategory": analytics["topCategory"],
        "categoryTotals": analytics["categoryTotals"],
        "averageTransaction": analytics["averageTransaction"],
        "budgetUtilizationPercent": round((total / budget_total) * 100, 1) if budget_total else 0,
    })


@app.route("/api/expenses", methods=["GET"])
def get_expenses():
    return jsonify({"transactions": transactions})


@app.route("/api/expenses", methods=["POST"])
def add_expense():
    data = request.get_json(silent=True) or {}
    validation_error = validate_expense(data)
    if validation_error:
        return jsonify({"error": validation_error}), 400

    new_txn = {
        "id":          generate_txn_id(),
        "title":       data["title"].strip(),
        "amount":      round(float(data["amount"]), 2),
        "category":    data.get("category", "Other"),
        "date":        data.get("date", datetime.now().strftime("%Y-%m-%d")),
        "description": data.get("description", ""),
    }
    transactions.insert(0, new_txn)
    return jsonify(new_txn), 201


@app.route("/api/expenses/<txn_id>", methods=["PUT"])
def update_expense(txn_id):
    data = request.get_json(silent=True) or {}
    validation_error = validate_expense(data, partial=True)
    if validation_error:
        return jsonify({"error": validation_error}), 400
    for i, t in enumerate(transactions):
        if t["id"] == txn_id:
            updatable = ["title", "amount", "category", "date", "description"]
            for field in updatable:
                if field in data:
                    value = round(float(data[field]), 2) if field == "amount" else data[field]
                    transactions[i][field] = value.strip() if field in ("title", "category") else value
            return jsonify(transactions[i])
    return jsonify({"error": f"Transaction {txn_id} not found."}), 404


@app.route("/api/expenses/<txn_id>", methods=["DELETE"])
def delete_expense(txn_id):
    for i, t in enumerate(transactions):
        if t["id"] == txn_id:
            transactions.pop(i)
            return jsonify({"deletedId": txn_id})
    return jsonify({"error": f"Transaction {txn_id} not found."}), 404


@app.route("/api/categories", methods=["GET"])
def get_categories():
    return jsonify({"categories": CATEGORIES})


@app.route("/api/analytics", methods=["GET"])
def analytics():
    return jsonify(compute_analytics(transactions))


@app.route("/api/predictions", methods=["GET"])
def predictions():
    analytics_data = compute_analytics(transactions)
    total_spend = analytics_data["totalSpend"]
    category_totals = analytics_data["categoryTotals"]

    # Simple linear projection: assume current month is ~40% complete
    # (11 days / ~30 days)
    days_elapsed = (datetime.now() - datetime.now().replace(day=1)).days + 1
    days_in_month = 30
    daily_rate = total_spend / days_elapsed if days_elapsed else 0
    predicted_total = round(daily_rate * days_in_month, 2)
    change_pct = round(((predicted_total - total_spend) / total_spend) * 100, 1) if total_spend else 0

    category_predictions = []
    for cat, spent in category_totals.items():
        predicted_cat = round((spent / days_elapsed) * days_in_month, 2) if days_elapsed else spent
        category_predictions.append({
            "category":  cat,
            "predicted": predicted_cat,
            "current":   spent,
        })

    return jsonify({
        "predictedNextMonthTotal": predicted_total,
        "previousMonthTotal":      total_spend,
        "changePercent":           change_pct,
        "confidenceScore":         72,
        "modelExplanation":        "Based on current month spending rate and historical patterns",
        "algorithmUsed":           "Linear trend projection",
        "categoryPredictions":     category_predictions,
    })


@app.route("/api/budget", methods=["GET"])
def budget():
    category_totals = compute_category_totals(transactions)
    budgets = []
    for cat in CATEGORIES:
        allocated = BUDGET_BASELINES.get(cat, 100)
        spent = category_totals.get(cat, 0)
        # Recommend slightly below current if over budget, else keep allocated
        recommended = round(min(allocated, spent * 0.9), 2) if spent > allocated else allocated
        budgets.append({
            "category":    cat,
            "allocated":   allocated,
            "spent":       spent,
            "recommended": recommended,
        })
    return jsonify({"budgets": budgets})


# ---------------------------------------------------------------------------
# /api/chat  – Groq-powered AI financial assistant
# ---------------------------------------------------------------------------

SYSTEM_PROMPT = """You are SpendWise AI, an expert personal finance assistant embedded in a financial management app. You have access to the user's real-time financial context including their monthly spending, budget, and transaction history.

Your role is to:
1. Analyze the user's spending patterns and provide actionable insights
2. Help them understand where their money goes
3. Predict future expenses and identify trends
4. Suggest practical budget optimizations
5. Identify unnecessary spending and recommend cuts
6. Answer any personal finance questions clearly and helpfully

Tone: Professional yet friendly. Use numbers from the context when available. Be specific, not generic.

When answering, use the financial context provided in the user message to give personalized responses. Format responses in clear paragraphs. Use bullet points for lists of recommendations. Keep responses concise but comprehensive (2-4 paragraphs max).

IMPORTANT: You are NOT a general AI assistant. Only answer questions related to personal finance, budgeting, spending analysis, savings, and financial planning. For unrelated topics, politely redirect to financial topics."""


def build_user_prompt(message: str, context: dict) -> str:
    total_monthly   = context.get("totalMonthlySpend", "N/A")
    remaining       = context.get("remainingBudget", "N/A")
    txn_count       = context.get("recentTransactionCount", "N/A")

    return (
        f"[Financial Context]\n"
        f"- Total Monthly Spend So Far: ${total_monthly}\n"
        f"- Remaining Budget: ${remaining}\n"
        f"- Number of Tracked Transactions: {txn_count}\n\n"
        f"[User Question]\n{message}"
    )


@app.route("/api/chat", methods=["POST"])
def chat():
    groq_api_key = os.getenv("GROQ_API_KEY", "")
    if not groq_api_key or groq_api_key == "your_groq_api_key_here":
        return jsonify({
            "error": "GROQ_API_KEY not configured. Please set it in backend/.env"
        }), 500

    data = request.get_json(silent=True) or {}
    if not isinstance(data, dict):
        return jsonify({"error": "Request body must be a JSON object."}), 400
    raw_message = data.get("message", "")
    if not isinstance(raw_message, str):
        return jsonify({"error": "Field 'message' must be a string."}), 400
    user_message = raw_message.strip()
    session_id   = data.get("sessionId", str(uuid.uuid4()))
    context      = data.get("context", {})

    if not user_message:
        return jsonify({"error": "Field 'message' is required."}), 400

    # Build / retrieve session history
    if not isinstance(user_message, str) or not user_message.strip():
        return jsonify({"error": "Field 'message' is required."}), 400
    if not isinstance(session_id, str) or not session_id.strip():
        return jsonify({"error": "Field 'sessionId' must be a non-empty string."}), 400
    if not isinstance(context, dict):
        return jsonify({"error": "Field 'context' must be a JSON object."}), 400

    history = chat_sessions.get(session_id, [])

    # Compose the full user message with injected context
    full_user_message = build_user_prompt(user_message, context)
    pending_history = history + [{"role": "user", "content": full_user_message}]

    # Keep only the last 10 messages (5 turns) to stay within token limits
    pending_history = pending_history[-10:]

    try:
        from groq import Groq  # type: ignore

        client = Groq(api_key=groq_api_key)
        response = client.chat.completions.create(
            model=os.getenv("GROQ_MODEL", "openai/gpt-oss-120b"),
            messages=[{"role": "system", "content": SYSTEM_PROMPT}] + pending_history,
            temperature=0.7,
            max_tokens=1024,
        )
        reply = response.choices[0].message.content
        pending_history.append({"role": "assistant", "content": reply})
        chat_sessions[session_id] = pending_history[-10:]

        return jsonify({
            "reply":          reply,
            "structuredData": None,
            "sessionId":      session_id,
        })

    except ImportError:
        return jsonify({
            "error": "groq package not installed. Run: pip install -r requirements.txt"
        }), 500
    except Exception as exc:
        return jsonify({"error": str(exc)}), 500


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    debug = os.getenv("FLASK_DEBUG", "1") == "1"

    groq_key = os.getenv("GROQ_API_KEY", "")
    key_ok = groq_key and groq_key != "your_groq_api_key_here"

    print("\n" + "=" * 55)
    print("  SpendWise AI — Flask Backend")
    print("=" * 55)
    print(f"  API:    http://localhost:{port}/api")
    print(f"  Health: http://localhost:{port}/api/health")
    print(f"  Groq:   {'✅ GROQ_API_KEY loaded — chatbot ready!' if key_ok else '❌ GROQ_API_KEY missing — set it in backend/.env'}")
    print("=" * 55 + "\n")

    app.run(host="0.0.0.0", port=port, debug=debug)
