# Third-party imports
from fastapi import FastAPI

# Local imports
from src.core.config import settings
from src.core.database import create_tables
from src.api.authentication import router as authentication_router
from src.api.questions import router as question_router
# from src.api.user_data import router as user_data_router
# from src.api.analytics import router as analytics_router
# from src.api.start_quiz import router as start_random_quiz_router


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
# app.include_router(user_data_router, prefix='/api/v1')
# app.include_router(analytics_router, prefix='/api/v1')
# app.include_router(start_random_quiz_router, prefix='/api/v1')

if __name__ == '__main__':
    import uvicorn
    uvicorn.run(
        app, host=settings.HOST.get_secret_value(), port=settings.PORT,
        reload=True
    )
