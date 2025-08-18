# Third-party imports
from fastapi import FastAPI

# Local imports
from src.core.config import settings
from src.core.database import create_tables
from src.api.authentication import router as authentication_router
from src.api.questions import router as question_router
from src.api.quiz_random import router as start_random_quiz_router
from src.api.quiz_category import router as start_category_quiz_router
from src.api.challenge_daily import router as start_challenge_daily_router
from src.api.multiplayer import router as multiplayer_router


create_tables()

app = FastAPI(
    title='Quiz Game API',
    description='Quiz Game Backend API',
    version='0.0.1'
)


@app.get('/')
def root():
    return {'message': 'Successfully running...', 'status': 'good'}


# Include routers
app.include_router(authentication_router, prefix='/api/v1')
app.include_router(question_router, prefix='/api/v1')
app.include_router(start_random_quiz_router, prefix='/api/v1')
app.include_router(start_category_quiz_router, prefix='/api/v1')
app.include_router(start_challenge_daily_router, prefix='/api/v1')
app.include_router(multiplayer_router, prefix='/api/v1')


if __name__ == '__main__':
    import uvicorn
    uvicorn.run(
        app, host=settings.HOST.get_secret_value(), port=settings.PORT,
        reload=True
    )
