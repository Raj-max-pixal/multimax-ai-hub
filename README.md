# Multimax AI Hub

A modern AI platform that brings multiple AI tools together into one cohesive interface.

## Features

- **AI Chat** - Chat with local models using Ollama
- **PDF Chat** - Upload and interact with your documents
- **Voice Assistant** - Speech-to-text transcription
- **Authentication** - Login/Signup with email, Google, and GitHub
- **Dark/Light Theme** - Toggle between themes
- **Responsive Design** - Works on mobile and desktop

## Tech Stack

### Frontend
- React 18 + TypeScript
- Vite
- Tailwind CSS
- React Router
- Framer Motion
- Lucide Icons
- Supabase

### Backend
- FastAPI (Python)
- Ollama integration

## Getting Started

### Prerequisites
1. Node.js 18+
2. Python 3.10+
3. Supabase account
4. Ollama (optional, for local AI)

### Frontend Setup

```bash
cd frontend
npm install
# Copy .env.example to .env and configure your Supabase credentials
npm run dev
```

### Backend Setup

```bash
cd backend
python -m venv venv
# Activate venv (Windows: venv\Scripts\activate | Mac/Linux: source venv/bin/activate)
pip install -r requirements.txt
# Copy .env.example to .env
uvicorn main:app --reload --port 8000
```

### Supabase Setup

1. Create a Supabase project at https://supabase.com
2. Copy your project URL and anon key
3. Configure authentication providers (Email, Google, GitHub)

## Project Structure

```
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   ├── contexts/
│   │   ├── pages/
│   │   ├── lib/
│   │   └── types/
│   └── package.json
├── backend/
│   ├── main.py
│   └── requirements.txt
└── README.md
```

## License

MIT
