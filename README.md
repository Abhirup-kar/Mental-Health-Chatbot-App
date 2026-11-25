# SereneMind — Mental Health Chatbot System

A full-stack **Mental Health Chatbot System** built with **HTML, CSS, JavaScript**, **Python / Flask**, **Rasa NLU & Custom Actions**, **VADER + domain sentiment analysis**, and **MySQL** (with automatic local SQLite fallback when MySQL is not running).

Users register and log in to a calm, private conversational interface where the Rasa-powered chatbot interacts like a supportive therapist, detects **Positive**, **Negative**, and **Neutral** sentiments plus communication patterns in real time, and recommends curated mental-health YouTube videos matched to the user's emotional state.

---

## Architecture & Project Structure

```text
pro5/
├── app/
│   ├── __init__.py            # Flask app factory & security headers
│   ├── auth.py                # Registration, login, logout & @login_required
│   ├── chat.py                # /chat UI + /api/chat, /api/sessions, /api/analytics, /api/videos
│   ├── config.py              # Environment-driven configuration (.env)
│   ├── db.py                  # MySQL (PyMySQL) + automatic SQLite fallback repository
│   ├── fallback_nlu.py        # Local TF-IDF NLU fallback using rasa_bot/data/nlu.yml
│   ├── rasa_client.py         # Rasa REST webhook & /model/parse client
│   ├── static/
│   │   ├── css/style.css      # Calm therapeutic UI theme & responsive layout
│   │   └── js/
│   │       ├── auth.js        # Password toggles & client validation
│   │       └── chat.js        # Messaging, SVG mood chart, video modal & voice input
│   └── templates/
│       ├── base.html
│       ├── index.html
│       ├── register.html
│       ├── login.html
│       └── chat.html
├── database/
│   └── schema.sql             # MySQL schema + 15 curated mental-health YouTube videos
├── rasa_bot/
│   ├── actions/actions.py     # Custom Rasa actions using shared sentiment engine
│   ├── data/
│   │   ├── nlu.yml            # 16 intents (~240 training examples)
│   │   ├── rules.yml          # Conversation rules + fallback action
│   │   └── stories.yml        # Multi-turn therapist flows
│   ├── config.yml             # DIETClassifier + TEDPolicy + FallbackClassifier
│   ├── credentials.yml        # REST channel enabled
│   ├── domain.yml             # Intents, slots, responses & actions
│   └── endpoints.yml          # Action server endpoint (:5055)
├── shared/
│   └── sentiment_engine.py    # Shared Positive/Negative/Neutral + pattern + crisis engine
├── scripts/
│   ├── init_mysql.py          # Initializes MySQL schema & seed videos
│   └── start_all.sh           # Launches Rasa Action Server, Rasa Server & Flask App
├── tests/                     # Automated pytest suite
├── .env.example
├── requirements.txt
└── run.py
```

---

## Quick Start

### 1. Environment Configuration (Optional MySQL / XAMPP)

Copy `.env.example` to `.env` if you want custom credentials:

```bash
cp .env.example .env
```

- **With MySQL / XAMPP running**:
  Start MySQL (e.g. XAMPP or `mysql-server`), set `MYSQL_HOST`, `MYSQL_USER`, `MYSQL_PASSWORD` in `.env`, and initialize the database:
  ```bash
  .venv/bin/python scripts/init_mysql.py
  ```
  (Or import `database/schema.sql` in phpMyAdmin / `mysql` CLI.)
- **Without MySQL running**:
  With `DB_BACKEND=auto` (default), the app automatically uses a local SQLite database at `instance/mental_health.db` with the exact same schema and 15 seeded videos.

### 2. Train the Rasa Model (if needed)

```bash
cd rasa_bot
TF_CPP_MIN_LOG_LEVEL=2 CUDA_VISIBLE_DEVICES=-1 .venv/bin/rasa train
cd ..
```

### 3. Run the Full System (Rasa Action Server + Rasa Server + Flask Web App)

```bash
chmod +x scripts/start_all.sh
./scripts/start_all.sh
```

Then open **http://127.0.0.1:5000** in your browser, register a new user account, log in, and start chatting.

### 4. Run Automated Tests

```bash
.venv/bin/pytest -v
```
