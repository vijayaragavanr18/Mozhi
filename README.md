# MozhiSense - Tamil Polysemy Learning Game

A modern, AI-powered educational platform for learning Tamil semantics and word sense disambiguation through interactive gameplay.

## 🎮 Features

- **Interactive Drag-and-Drop Challenges**: Learn Tamil polysemy through engaging gameplay
- **Semantic Graph Visualization**: Explore relationships between word meanings visually
- **AI-Powered Distractors**: Intelligent wrong answers generated using Ollama
- **Morphological Learning**: Understand Tamil word inflections and derivations
- **User Progress Tracking**: Monitor learning stats, accuracy, and word mastery
- **Real-time Feedback**: Immediate validation of answers with learning explanations

## 📁 Project Structure

```
MozhiSense/
├── mozhisense-backend/          # FastAPI Backend
│   ├── main.py                  # FastAPI app entry point
│   ├── requirements.txt          # Python dependencies
│   ├── .env                      # Environment variables
│   ├── db/
│   │   ├── database.py          # SQLite initialization
│   │   ├── wordnet.json         # Tamil word definitions & senses
│   │   └── mozhisense.db        # SQLite database
│   └── engine/
│       ├── sense_engine.py      # Word sense management
│       ├── morphology_engine.py # Tamil inflection generator
│       ├── ai_generator.py      # Ollama integration for distractors
│       ├── bias_controller.py   # Answer distribution balancer
│       ├── distractor_selector.py # Smart wrong answer selection
│       ├── validator.py         # Challenge validation
│       ├── wordnet_fetcher.py   # WordNet data loader
│       └── wordnet_expander.py  # WordNet expansion utilities
│
└── Frontend_Sense/              # React 18 + Vite Frontend
    ├── package.json
    ├── vite.config.ts
    ├── .env                     # Frontend config
    ├── index.html
    ├── src/
    │   ├── App.jsx
    │   ├── main.jsx
    │   ├── index.css
    │   ├── data.js              # Mock data
    │   ├── api/
    │   │   ├── config.js        # API base URL
    │   │   └── mozhisense.js    # Complete API client
    │   ├── components/
    │   │   ├── TopBar.jsx
    │   │   └── BottomNav.jsx
    │   └── screens/
    │       ├── HomeScreen.jsx   # Word list & featured lesson
    │       ├── PlayScreen.jsx   # Interactive challenges
    │       ├── ExploreScreen.jsx # Semantic graph explorer
    │       └── ProfileScreen.jsx # User stats & mastery
```

## 🚀 Quick Start

### Prerequisites
- Python 3.12+
- Node.js 18+
- Ollama (for AI distractors)
- SQLite3

### Backend Setup

```bash
cd mozhisense-backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Start backend
uvicorn main:app --reload --port 8000
```

Backend will be available at: **http://localhost:8000**
- API Docs: http://localhost:8000/docs

### Frontend Setup

```bash
cd Frontend_Sense

# Install dependencies
npm install

# Start dev server
npm run dev
```

Frontend will be available at: **http://localhost:5173**

## 🔌 API Endpoints

### Words
- `GET /words` - List all Tamil words
- `GET /words/search?q=<query>` - Search by word or meaning
- `GET /words/<word>/senses` - Get all senses for a word

### Challenges
- `GET /challenges/<word>` - Get challenges for a word
- `GET /challenges/<word>/<sense_id>` - Challenge for specific sense

### Semantic Graph
- `GET /graph/<word>` - Get semantic relationships (nodes & edges)

### Sessions & Learning
- `POST /sessions/attempt` - Record an answer attempt
- `GET /sessions/<user_id>/stats` - User statistics
- `GET /sessions/<user_id>/weakspots` - Words needing practice

## 🛠️ Technology Stack

### Backend
- **FastAPI** - Async Python web framework
- **SQLite** - Lightweight database
- **Stanza** - NLP for Tamil parsing
- **Ollama** - Local LLM for distractors
- **scikit-learn** - ML utilities
- **Pydantic** - Data validation

### Frontend
- **React 18** - UI framework
- **Vite** - Build tool
- **Tailwind CSS** - Styling
- **dnd-kit** - Drag-and-drop
- **Framer Motion** - Animations
- **Lucide Icons** - Icon library

## 📊 Data

### WordNet Structure
```json
{
  "கல்": {
    "transliteration": "kal",
    "senses": [
      {
        "id": "kal_n1",
        "pos": "Noun",
        "meaning_en": "stone",
        "meaning_ta": "கற்கட்டி",
        "example_en": "The stone is hard",
        "example_ta": "கல் கடினமாக உள்ளது"
      }
    ]
  }
}
```

## 🔄 Challenge Generation Pipeline

1. **Select Word & Sense** - Choose target word and its meaning
2. **Generate Sentence** - Create Tamil sentence with blank
3. **Generate Morphological Distractors** - Use word inflection variations
4. **Generate AI Distractors** - Use Ollama for semantic confusion
5. **Select Cross-POS Senses** - Include other word senses as options
6. **Shuffle & Validate** - Randomize and validate challenge integrity

## 📈 Features Implemented

✅ Backend verification (9 checks)
✅ Frontend API integration
✅ All components connected to API
✅ CORS configured for localhost:5173
✅ Loading and error states
✅ End-to-end testing
✅ Database initialization
✅ Sense engine functional
✅ Morphology engine working
✅ AI generator with Ollama

## 🔐 Environment Setup

**Backend (.env)**
```
OLLAMA_BASE_URL=http://localhost:11434
DATABASE_PATH=db/mozhisense.db
```

**Frontend (.env)**
```
VITE_API_URL=http://localhost:8000
```

## 📝 License

Educational Project - Tamil Language Learning

## 👤 Author

Vijay Agaravan

## 🔗 Resources

- [Tamil Language](https://en.wikipedia.org/wiki/Tamil_language)
- [WordNet for Indian Languages](https://indwordnet.github.io/)
- [Ollama](https://ollama.ai)
- [FastAPI](https://fastapi.tiangolo.com/)
- [React](https://react.dev)

---

**Status**: ✅ Ready for Development & Testing

Built with ❤️ for Tamil language learning.
