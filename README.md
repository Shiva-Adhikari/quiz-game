# 🎯 Quiz Game API

A comprehensive quiz application backend built with **FastAPI**, **PostgreSQL**, and modern Python technologies. Perfect for educational platforms, competitive quizzing, and gamified learning experiences.

## 🚀 Live Demo
- **API Documentation:** [https://quiz-game-1-9tz8.onrender.com]
- **Interactive Swagger UI:** [https://quiz-game-1-9tz8.onrender.com/docs]
- **ReDoc Documentation:** [https://quiz-game-1-9tz8.onrender.com/redoc]

## ✨ Features

### 🔐 Authentication & User Management
- **Secure Registration/Login** with JWT tokens
- **User Profiles** with customizable settings
- **Role-based access** control

### 🎮 Quiz Experience
- **Category-wise Quizzes** - Organized by topics
- **Random Quiz Mode** - Mixed questions for variety
- **Difficulty Levels** - Easy, Medium, Hard progression
- **Smart Timer System** - Configurable time limits
- **Real-time Question Delivery**

### 🏆 Scoring & Competition
- **Dynamic Leaderboards** - Global and category-wise rankings
- **Comprehensive Results** - Detailed performance analytics
- **Progress Tracking** - Historical score analysis
- **Ranking System** - Competitive positioning

### 🎁 Gamification & Rewards
- **Daily Challenges** - Fresh content every day
- **XP System** - Experience points for engagement
- **Badge Collection** - Achievement-based rewards
- **Virtual Currency** - Coins for premium features
- **Level Progression** - User advancement system

### 👥 Social Features
- **Multiplayer Mode** - Real-time competitive quizzing
- **Challenge Friends** - Direct player-vs-player
- **Community Leaderboards**

## 🛠️ Tech Stack

```
Backend:     FastAPI, Python 3.11+
Database:    PostgreSQL with SQLAlchemy ORM
Validation:  Pydantic v2
Auth:        JWT with bcrypt hashing
Testing:     Pytest
Documentation: Auto-generated OpenAPI/Swagger
```

## 📋 Prerequisites

- Python 3.11+
- PostgreSQL 12+
- pip or conda or uv

## 🚀 Quick Start

### 1. Clone Repository
```bash
git clone https://github.com/Shiva-Adhikari/quiz-game.git
cd quiz-game
```

### 2. Setup Environment
```bash
# Install dependencies
pip install uv
uv sync
```

### 3. Database Configuration
```bash
# Create PostgreSQL database
createdb quiz_game_db

# Set environment variables
export DATABASE_URL="postgresql://username:password@localhost/quiz_game_db"
export SECRET_KEY="your-secret-key-here"
```

### 4. Run Application
```bash
# Start development server with uv
uv run uvicorn main:app --reload --host 0.0.0.0 --port 8000
# Or 
python -m uv run uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### 5. Access API
- **API Base:** http://localhost:8000
- **Interactive Docs:** http://localhost:8000/docs
- **Alternative Docs:** http://localhost:8000/redoc

## 📚 API Endpoints

### Authentication
```http
POST /api/v1/register          # User registration
POST /api/v1/login            # User login
GET  /api/v1/profile          # Get user profile
PUT  /api/v1/profile          # Update profile
```

### Quiz Management
```http
GET  /api/v1/categories       # List quiz categories
GET  /api/v1/quiz/random      # Start random quiz
GET  /api/v1/quiz/category/{id} # Start category quiz
POST /api/v1/quiz/submit      # Submit quiz answers
```

### Game Features
```http
GET  /api/v1/leaderboard      # Global rankings
GET  /api/v1/daily-challenge  # Today's challenge
GET  /api/v1/badges          # User achievements
POST /api/v1/multiplayer/join # Join multiplayer game
```

## 🏗️ Project Structure

```
quiz-game/
├── src/
│   ├── api/                 # API route handlers
│   │   ├── authentication.py
│   │   ├── questions.py
│   │   ├── quiz_random.py
│   │   ├── multiplayer.py
│   │   └── leaderboard.py
│   ├── core/               # Core configuration
│   │   ├── config.py
│   │   ├── database.py
│   │   └── security.py
│   ├── models/             # Database models
│   ├── schemas/            # Pydantic schemas
│   ├── services/
│   └── utils/
├── tests/                  # Test suite
├── main.py                 # Application entry point
├── pyproject.toml          # Dependencies
└── README.md               # This file
```

## 🧪 Running Tests 'Not Available'

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src tests/

# Run specific test file
pytest tests/test_authentication.py
```

## 🐳 Docker Deployment 'Not Available'

```bash
# Build image
docker build -t quiz-game-api .

# Run with docker-compose
docker-compose up -d
```

## 🔧 Configuration

Key environment variables:

```env
# === Database ===
DATABASE_URL='postgresql://username:password@localhost:5432/database-name'

# === Server Configuration ===
HOST='localhost'
PORT=8000
DEBUG=False

# === OTP Configuration ===
# Expiration time in hour
OTP_EXPIRE=1

# === Email ===
SENDER_EMAIL='your-email@gmail.com'
SENDER_PASSWORD='your-app-password'
EMAIL_HOST='smtp.gmail.com'     # Google
EMAIL_PORT=465     # Use 587 for TLS, 465 for SSL

# === Room settings ===
ROOM_CODE_LENGTH=8
MAX_PLAYERS_PER_ROOM=6
MIN_PLAYERS_PER_ROOM=2
DEFAULT_QUESTION_TIME=30
ROOM_IDLE_TIMEOUT=300  # 5 minutes
QUESTION_TIMEOUT_BUFFER=3  # seconds

# === Score calculation ===
BASE_CORRECT_SCORE=100
SPEED_BONUS_MAX=50
WRONG_ANSWER_PENALTY=0

# === JWT settings ===
SECRET_KEY='your-secret-key'
ALGORITHM="HS256"
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

## 🔜 Upcoming Features

- [ ] Real-time notifications
- [ ] Mobile app integration
- [ ] Advanced analytics dashboard
- [ ] AI-powered question generation
- [ ] Social media integration
- [ ] Offline mode support

## 👨‍💻 Developer

**Shiva Adhikari**
- GitHub: [@Shiva-Adhikari](https://github.com/Shiva-Adhikari)
- Email: [shivaadhikari@duck.com]

## 🙏 Acknowledgments

- FastAPI for the amazing framework
- SQLAlchemy for robust ORM
- PostgreSQL for reliable data storage

---

*Built with ❤️ using FastAPI and modern Python*

