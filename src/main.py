# Third-party imports
import uvicorn
from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware

# Local imports
from src.core.config import settings
from src.core.database import create_tables
from src.api.authentication import router as authentication_router
from src.api.questions import router as question_router
from src.api.quiz_random import router as start_random_quiz_router
from src.api.quiz_category import router as start_category_quiz_router
from src.api.challenge_daily import router as start_challenge_daily_router
from src.api.multiplayer import router as multiplayer_router
from src.api.user_profile import router as user_profile_router
from src.api.level_system import router as level_system_router
from src.api.badges import router as badges_router


create_tables()

app = FastAPI(
    title='Quiz Game API',
    description='Quiz Game Backend API',
    version='0.0.1'
)

# Add CORS middleware to allow cross-origin requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify actual origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get('/')
def root():
    return {'message': 'Successfully running...', 'status': 'good'}

@app.get("/favicon.ico")
async def favicon():
    return FileResponse("path/to/favicon.ico")


# Include routers
app.include_router(authentication_router, prefix='/api/v1')
app.include_router(question_router, prefix='/api/v1')
app.include_router(start_random_quiz_router, prefix='/api/v1')
app.include_router(start_category_quiz_router, prefix='/api/v1')
app.include_router(start_challenge_daily_router, prefix='/api/v1')
app.include_router(multiplayer_router, prefix='/api/v1')
app.include_router(user_profile_router, prefix='/api/v1')
app.include_router(level_system_router, prefix='/api/v1')
app.include_router(badges_router, prefix='/api/v1')


if __name__ == '__main__':
    uvicorn.run(
        app, host=settings.HOST.get_secret_value(), port=settings.PORT,
        reload=True
    )
