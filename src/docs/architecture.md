PROJECT-NAME/
│
├── src/
│   │
│   ├── api/                   # Route definitions (divided by feature)
│   │   ├── dependencies/
│   │   │   ├── __init__.py
│   │   │   ├── auth.py
│   │   │   └── database.py
│   │   │
│   │   ├── v1/
│   │   │   ├── __init__.py
│   │   │   └── endpoints/
│   │   │       ├── user.py
│   │   │       ├── user.py
│   │   │       ├── auth.py             # login, logout, refresh
│   │   │       ├── admin.py            # admin-only stuff
│   │   │       └── leaderboard.py
│   │   └── v2/
│   │
│   │
│   ├── core/                      # Core config, settings, security
│   │   ├── config.py              # Env settings (like DB_URL, secret keys)
│   │   ├── security.py            # JWT, password hashing, auth utils
│   │   ├── logger.py              # logging Module
│   │   ├── database.py            # DB connection (if using SQL or Beanie)
│   │   ├── exception_handlers.py  # Custom error responses
│   │   └── middleware.py          # Global middlewares like CORS, timers
│   │
│   │
│   ├── models/                 # DB Models (SQLAlchemy, Pydantic)
│   │   ├── __init__.py         # Combine all models for easy import
│   │   ├── user.py             # User table/document
│   │   ├── quiz.py             # Quiz questions and answers
│   │   ├── result.py           # Stores user’s quiz results
│   │   ├── token.py            # Optional: store refresh tokens (if needed)
│   │   ├── leaderboard.py      # Ranks, scores, XP, etc.
│   │   └── admin.py            # Admin accounts or admin logs
│   │
│   │
│   ├── schemas/                # Pydantic schemas for input/output
│   │   ├── __init__.py         # Optional – for easier imports
│   │   ├── user.py             # UserCreate, UserLogin, UserOut, profile schemas
│   │   ├── quiz.py             # QuizCreate, QuizOut, QuizSubmit, QuizFetch
│   │   ├── result.py           # QuizResult, QuizResultOut | User quiz result schema
│   │   ├── token.py            # TokenData, TokenRequest
│   │   ├── leaderboard.py      # XP, coins, ranking | # LeaderboardOut
│   │   └── admin.py            # AdminLogin, AdminOut | # Admin login/profile
│   │
│   │
│   ├── crud/                   # DB operations (create, read, update, delete)
│   │   ├── __init__.py         # Optional – for easier imports
│   │   ├── user.py             # create_user, get_user_by_email
│   │   ├── quiz.py             # create_quiz, get_random_quiz
│   │   ├── result.py           # save_quiz_result, get_user_results
│   │   ├── token.py            # save_refresh_token, get_token_by_string
│   │   ├── leaderboard.py      # get_leaderboard, update_user_xp
│   │   └── admin.py            # get_admin_by_email
│   │
│   │
│   ├── services/                   # Business logic
│   │   ├── __init__.py             # Optional – for easier imports
│   │   ├── user_service.py         # User registration, profile logic | get_profile
│   │   ├── quiz_service.py         # Quiz fetch/submit logic | fetch_quiz, add_quiz
│   │   ├── result_service.py       # Calculate and save results | submit_quiz logic
│   │   ├── token_service.py        # JWT logic (not in core) | # generate tokens
│   │   ├── leaderboard_service.py  # XP, coins, rank updates | # fetch and reward XP
│   │   └── admin_service.py        # Admin logic (auth, dashboard) | # login admin
│   │
│   │
│   ├── deps/                   # Dependencies used in routes
│   │   ├── __init__.py         # Optional – for easier imports
│   │   ├── db.py               # Get DB session for routes/services
│   │   ├── auth.py             # Get current user from token
│   │   ├── admin.py            # Verify current user is admin
│   │   └── rate_limit.py       # Optional: custom rate limiter logic
│   │
│   │
│   ├── tests/                  # Unit + integration tests
│   │   ├── __init__.py         # Optional – for easier imports
│   │   ├── test_user.py
│   │   └── test_quiz.py
│   │
│   │
│   ├── utils/
│   │   ├── __init__.py     # Optional – for easier imports
│   │   ├── email.py            # Send email function (for OTP, verify, etc.)
│   │   ├── formatter.py        # Text, date, number formatting
│   │   ├── randomizer.py       # Generate random strings, codes, tokens
│   │   ├── file.py             # File handling utilities (image save, delete)
│   │   └── validator.py        # Custom validation logic (non-pydantic)
│   │
│   │
│   ├── email_templates/            # Optional
│   │   ├── __init__.py                 # Optional – for easier imports
│   │   ├── base_template.html          # common layout (optional)
│   │   ├── welcome_email.html          # for new registered users
│   │   ├── reset_password_email.html   # when user requests password reset
│   │   ├── otp_email.html              # for sending OTP codes
│   │   └── verify_email.html           # email verification with link
│   │
│   │
│   ├── docs/                             # Optional
│   │   ├── __init__.py                       # optional
│   │   ├── architecture.md                   # Folder & file structure (this one 💯)
│   │   ├── api_endpoints.md                  # All API route docs with examples
│   │   ├── auth_flow.md                      # Login/register + JWT refresh flow
│   │   ├── db_schema.png                     # (Optional) ER diagram or DB model diagram
│   │   ├── setup_guide.md                    # How to install, run, test app
│   │   ├── email_templates_preview.md        # Screenshots or HTML previews
│   │   └── project_notes.md                  # To-do list, bugs, future features
│   │
│   │
│   ├── scripts/            # Optional
│   ├── events/             # Optional
│   ├── middleware/         # Optional
│   ├── exceptions/         # Optional
│   ├── permissions/        # Optional
│   └── alembic/            # DB migration files (optional)
│       └── versions/
│
│
├────── main.py                   # FastAPI app entry point
├────── __init__.py               # Optional – for easier imports
├────── .env                      # Environment variables (loaded in config.py)
├────── requirements.txt          # Installed packages list | # Project dependencies
├────── alembic.ini               # Alembic config file (if using Alembic) | DB migrations
└────── README.md                 # Project instructions
