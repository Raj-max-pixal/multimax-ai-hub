<<<<<<< HEAD
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
=======
<div align="center">

# ⚡ Multimax AI Hub

### The All-in-One AI Workspace

Build. Create. Code. Research. Automate.

<p>
  <img src="https://img.shields.io/badge/Status-Active-success?style=for-the-badge" />
  <img src="https://img.shields.io/badge/Version-v1.0-blue?style=for-the-badge" />
  <img src="https://img.shields.io/badge/License-MIT-orange?style=for-the-badge" />
</p>

<p>
  <strong>One intelligent workspace for everything AI.</strong>
</p>

</div>

---

## 🚀 Overview

Multimax AI Hub is a modern AI platform designed to bring the most powerful AI capabilities into one seamless experience.

Whether you're a developer, student, creator, researcher, or business professional, Multimax AI Hub helps you work faster with intelligent tools powered by advanced AI.

---

## ✨ Features

- 💬 AI Chat Assistant
- 🤖 Multiple AI Models
- 🧠 AI Agents
- 💻 Coding Assistant
- 📄 PDF & Document Analysis
- 🎤 Voice Conversations
- 🖼️ AI Image Generation
- 🎥 AI Video Generation
- ✍️ Content Writing
- 🌐 Web Search
- 📁 File Upload & Analysis
- 💾 Chat History
- 🔒 Secure Authentication
- 🌙 Modern Dark UI
- 📱 Responsive Design

---

## 🛠 Tech Stack

### Frontend

- React
- Next.js
- TypeScript
- Tailwind CSS

### Backend

- Node.js
- Firebase
- REST APIs

### AI

- Gemini
- OpenAI Compatible APIs
- AI Agents
- Multimodal Models

---

## 📸 Screenshots

> Add screenshots here.

| Home | Chat |
|------|------|
| Image | Image |

---

## 📈 Roadmap

- [x] AI Chat
- [x] Authentication
- [x] Responsive UI
- [ ] AI Voice Assistant
- [ ] Image Generation
- [ ] Video Generation
- [ ] AI Workspace
- [ ] Browser Extension
- [ ] Desktop Application
- [ ] Mobile App

---

## ⚙️ Installation

```bash
git clone https://github.com/yourusername/multimax-ai-hub.git

cd multimax-ai-hub

npm install

npm run dev
```

---

## 📂 Project Structure

```
src/
 ├── app/
 ├── components/
 ├── hooks/
 ├── services/
 ├── utils/
 ├── assets/
 └── types/
```

---

## 🌍 Vision

Multimax AI Hub is the first step toward building the Multimax ecosystem—a unified suite of AI-powered products designed to simplify creation, productivity, and automation.

Future products include:

- ☁️ Multimax Cloud
- 📄 Multimax Office
- 💾 Multimax Drive
- 💬 Multimax Connect
- 🎮 Multimax Gaming
- 💻 Multimax Studio

---

## 🤝 Contributing

Contributions, ideas, and feedback are always welcome.

Feel free to open an issue or submit a pull request.

---

## ⭐ Support

If you like this project, please consider giving it a ⭐ on GitHub.

It helps the project grow and motivates future development.

---

<div align="center">

### Built with ❤️ by Multimax

**Beyond Tech. Beyond Limit.**

</div>
>>>>>>> 461cffab37c6ce39b6b4393e7f328d1036ff2296
