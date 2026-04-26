# 🚀 AI Interview Coach – Full-Stack Project

> **Frontend:** React + Vite + Tailwind CSS  
> **Backend:** FastAPI + Python  
> **Database:** In-memory sessions (JSON files)

## ⭐ Features (What it does)

- **Resume Parsing:** Upload PDF/DOCX → extract skills, experience, education → build structured profile.
- **AI Interviewer:** Generates questions from your resume, asks them one by one, listens to your spoken answers.
- **Live Feedback:** Real-time scoring (1–10) + detailed notes per answer (strengths, weaknesses, improvements).
- **Verbal Reactions:** AI interviewer gives short spoken reactions after each answer (e.g., “Good start, but could be more specific.”).
- **Endless Practice:** “Next Question” button generates fresh interview questions based on your resume + topic.
- **Voice:** Includes basic text-to-speech for natural voice interaction.

## 📂 Project Structure

```
ai-interview-prep/
├── backend/                 # FastAPI server
│   ├── app/
│   │   ├── config.py        # Env vars, AI prompts
│   │   ├── main.py          # FastAPI app entry
│   │   ├── services/
│   │   │   ├── resume_parser.py
│   │   │   ├── ai_service.py    # OpenAI calls
│   │   │   ├── delivery_analyser.py  # Algorithmic analysis
│   │   │   ├── content_analyser.py
│   │   │   ├── tts_service.py    # Text-to-Speech
│   │   │   ├── session_store.py  # JSON session storage
│   │   ├── routes/
│   │   │   ├── resume.py
│   │   │   ├── interview.py
│   │   │   ├── feedback.py
│   │   │   ├── sessions.py
│   │   │   ├── voice.py
│   ├── requirements.txt
│   └── .env                 # API keys, etc.
│
└── src/                     # React frontend
    ├── hooks/
    │   ├── useSpeechRecognition.js
    │   ├── useTimer.js
    │   └── useTTS.js
    ├── components/
    │   ├── ResumeUpload.jsx
    │   ├── InterviewRoom.jsx
    │   ├── QuestionBank.jsx
    │   ├── FeedbackView.jsx
    │   └── ChatHistory.jsx
    ├── utils/
    │   ├── api.js
    │   └── resumeProcessor.js
    ├── App.jsx
    ├── main.jsx
    └── index.html
```

## 🛠️ Tech Stack

### Backend
- **Framework:** FastAPI (Python)
- **AI:** OpenAI SDK (GPT-4o / GPT-3.5)
- **Parsing:** PyMuPDF (PDF), python-docx (Word)
- **TTS:** `edge-tts` (Microsoft Neural voices)
- **Storage:** In-memory JSON session files (`.json` in `sessions/`)
- **Server:** Uvicorn + Gunicorn

### Frontend
- **Framework:** React 18 + Vite
- **Styling:** Tailwind CSS
- **Speech:** Web Speech API (`SpeechRecognition`)
- **State:** Local component state + JSON session fetching
- **Packages:** Axios, react-router-dom, etc.

## 🚀 Setup Instructions

### 1. Backend Setup

```bash
# Create virtual environment
python -m venv .env
source .env/Scripts/activate

# Install backend dependencies
pip install -r backend/requirements.txt

# Create .env file (if missing)
cp backend/.env.example backend/.env

# Fill in your OpenAI API key in backend/.env:
OPENAI_API_KEY=your_openai_key_here

# Run the server
cd backend
uvicorn app.main:app --reload
```

Backend will run at: `http://localhost:8000`

### 2. Frontend Setup

```bash
# Navigate to frontend
cd ai-interview-prep

# Install frontend dependencies
npm install

# Create .env file (if missing)
cp .env.example .env

# Ensure VITE_API_URL points to backend:
# VITE_API_URL=http://localhost:8000

# Start the React dev server
npm run dev
```

Frontend will run at: `http://localhost:5173`

## 🧪 How to Test

### A. Upload Resume
1. Open frontend → go to **Upload Resume**.
2. Select PDF or DOCX.
3. Click **Parse Resume**.
4. The UI should show parsed skills, experience, and a profile summary.

### B. Start Interview
1. Navigate to **Interview Room**.
2. Select a topic (e.g., “Tell me about yourself”, “Strengths & Weaknesses”).
3. Click **Start Interview**.
4. The backend will generate questions based on your resume.

### C. Answer Questions
1. Click **Record** to start speaking.
2. Click **Stop** when finished.
3. Click **Submit & Get Feedback**.
4. The AI will:
   - Score your answer.
   - Provide detailed notes (strengths / areas to improve).
   - Play a spoken reaction (if TTS is working).
5. Click **Next Question** to continue the interview.

## 📞 API Endpoints (for reference)

### Resume Routes
```
POST /api/resume/parse   → Upload resume and parse it
GET /api/resume/status/:job_id → Check upload status

POST /api/resume/upload_url   → Generate upload URL (AWS S3)
```

### Interview Routes
```
GET /api/interview/questions?resume_id=...&topic=... → Generate questions
POST /api/interview/feedback   → Get AI feedback on answer
POST /api/interview/start       → Start a mock interview session
POST /api/interview/next-question → Ask next AI-generated question
```

### Session Routes
```
GET /api/sessions               → List all sessions
GET /api/sessions/:id           → Get session by ID
POST /api/sessions/:id/reset    → Clear session
```

### Voice Routes
```
GET /api/tts/voices             → List available TTS voices
POST /api/tts                   → Convert text-to-speech (streaming)
```

## ⚡ Key Features Deep Dive

### Resume Parsing
- Uses LLM to extract contextually meaningful skills and experiences.
- Supports both **PDF** and **DOCX** files.
- Generates a clean JSON profile used to tailor interview questions.

### Delivery Analysis (Algorithmic)
Even before AI scoring, the backend performs:
- **Pace:** Words Per Minute (WPM) based on transcript length + duration.
- **Filler Words:** Counts `um`, `uh`, `like`, `you know`, etc.
- **Confidence:** Detects strong vs weak phrasing.
- **Repetition:** Flags repeated phrases.
- **Vocabulary Richness:** Type-Token Ratio (TTR).
- **STAR Method:** Detects Situation/Task/Action/Result signals.

### AI Feedback Loop
1. User submits answer.
2. Backend sends transcript + delivery analysis + session context to OpenAI.
3. AI returns:
   - Score (1–10)
   - Strengths
   - Improvements
   - Interviewer reaction
4.Frontend displays everything in a clean UI.

## 🐛 Troubleshooting

### Frontend CORS error
Ensure `backend/.env` has:
```
OPENAI_API_KEY=your_key

# CORS should allow frontend origin
ALLOWED_ORIGINS=http://localhost:5173
```
And frontend `.env` has:
```
VITE_API_URL=http://localhost:8000
```

### TTS not working
- Ensure `edge-tts` is installed (`pip install edge-tts`).
- Ensure you have an internet connection (it uses Microsoft Azure).
- Some corporate networks block WebSocket traffic; try on a different network if needed.

### No questions generated
Make sure you have:
1. Uploaded a resume successfully.
2. Selected a topic.
3. Clicked 