# Third-party imports
from fastapi import FastAPI

# Local imports
from src.core.config import settings
from src.core.database import create_tables
from src.api.user import router as user_router


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
app.include_router(user_router, prefix='/api/v1')

if __name__ == '__main__':
    import uvicorn
    uvicorn.run(
        app, host=settings.HOST.get_secret_value(), port=settings.PORT,
        reload=True
    )
