# HW 4 — Campus Customs Shop + Chatbot

A storefront for Campus Customs, a student-run Yale merch shop. It has a **React + Vite + TypeScript** front end and a **FastAPI** back end whose chatbot ("Dan") is a **PydanticAI** agent. Dan answers price and stock questions from the SQLite database and puts matching products on the page as cards.

## Layout

```
hw4/
├── AI_prompts.md          # every prompt I gave my vibe coder, per problem
├── requirements.txt       # Python back-end dependencies
├── .env.example           # copy to .env and add your key
├── .gitignore             # excludes .env, data/ (db + images), .venv, node_modules
├── README.md
├── frontend/              # Vite React TypeScript app
├── backend/
│   ├── main.py            # FastAPI app — run with: uvicorn main:app --reload --port 8000
│   ├── agent.py           # agent wiring: model, prompt, deps, audit trail
│   ├── models.py          # Pydantic / PydanticAI types
│   ├── tools.py           # database access + agent tools
│   └── prompts/
│       └── prompt.md      # system prompt (voice, tool rules, safety)
└── output/
    ├── harness.md         # how the whole system works
    ├── design.md
    ├── usability.md
    ├── app_check.html     # open by double-clicking
    ├── app_check_images/
    └── audit_trail.json   # append-only agent activity log
```

## 1. Put the data pack in place (not in git)

Download `data.zip` from the course site and unzip it **inside `hw4/`** so you have:

```
hw4/data/campus_customs.db
hw4/data/products/*.jpg
```

## 2. Add your API key

```bash
cd hw4
cp .env.example .env      # then edit .env and paste your PORTKEY_API_KEY
```

The back end also finds a `.env` in a parent folder if `hw4/.env` doesn't exist.

## 3. Run the back end (terminal 1)

Requires Python 3.11+ (built with 3.13).

```bash
cd hw4
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cd backend
uvicorn main:app --reload --port 8000
```

Check it: <http://127.0.0.1:8000/api/health> → `{"ok": true, ...}`. Interactive API docs: <http://127.0.0.1:8000/docs>.

## 4. Run the front end (terminal 2)

Requires Node 20+.

```bash
cd hw4/frontend
npm install
npm run dev
```

Open <http://localhost:5173>. Vite proxies `/api` and `/media` to the back end on port 8000, so keep both running.

## Try it

- **Test account:** `test@campuscustoms.yale.edu` / `password` (from the seed database), or create your own.
- **Chat (paw button, bottom right):**
  - "What hoodies do you have?" → cards appear in "Dan's picks" on the page.
  - On a product page: "Do you have this in XS?" → honest stock, plus in-stock alternatives if it's sold out.
  - Logged in: your chat is saved and comes back next visit.

See `output/harness.md` for how it all works.
