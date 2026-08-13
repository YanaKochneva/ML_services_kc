# api.py
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from routes.balance import balance_route
from routes.user import user_route
from routes.ml_task import ml_task_route
from routes.transaction import transaction_route
from routes.auth import auth_route
from database.database import init_db, get_session
from database.config import get_settings
from services.crud.llm_config import get_all_llm_configs
import uvicorn
import logging

logger = logging.getLogger(__name__)
settings = get_settings()

def create_application() -> FastAPI:
    app = FastAPI(
        title=settings.APP_NAME,
        description=settings.APP_DESCRIPTION if hasattr(settings, 'APP_DESCRIPTION') else "ML Services API",
        version=settings.API_VERSION,
        docs_url="/api/docs",
        redoc_url="/api/redoc"
    )

    app.mount("/view", StaticFiles(directory="view"), name="view")
    # templates = Jinja2Templates(directory="view")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(user_route, prefix='/api/users', tags=['Users'])
    app.include_router(transaction_route, prefix='/api/transactions', tags=['Transactions'])
    app.include_router(ml_task_route, prefix='/api/ml-tasks', tags=['ML Tasks'])
    app.include_router(balance_route, prefix='/api/balance', tags=['Balance'])
    app.include_router(auth_route, prefix='/api/auth', tags=['Auth'])

    @app.get('/health')
    def health():
        return {'status': 'healthy'}

    @app.get("/")
    async def index():
        return FileResponse("view/index.html")

    @app.get("/api/llm-configs", tags=["LLM"])
    def get_llm_configs():
        with get_session() as session:
            configs = get_all_llm_configs(session, active_only=True)
            return [{"id": c.id, "name": c.name, "cost": c.cost_per_request} for c in configs]

    return app

app = create_application()

@app.on_event("startup") 
def on_startup():
    try:
        logger.info("Initializing database...")
        init_db()
        logger.info("Application startup completed successfully")
    except Exception as e:
        logger.error(f"Startup failed: {str(e)}")
        raise
    
@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Application shutting down...")

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    uvicorn.run(
        'api:app',
        host='0.0.0.0',
        port=8080,
        reload=True,
        log_level="info"
    )