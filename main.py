import uvicorn
from fastapi import FastAPI
from scalar_fastapi import get_scalar_api_reference
from contextlib import asynccontextmanager
from src.user.api import user_router
from src.db.manager.manager import db_manager


@asynccontextmanager
async def lifespan(app: FastAPI):
    db_manager.init_db()
    yield
    await db_manager.close_db()


app = FastAPI(
    title="User Service",
    docs_url=None,
    lifespan=lifespan,
)

app.include_router(
    user_router,
    tags=["User"],
)


@app.get("/docs", include_in_schema=False)
async def scalar_html():
    return get_scalar_api_reference(
        openapi_url=app.openapi_url if app.openapi_url else "/openapi.json",
        title=app.title,
    )


if __name__ == "__main__":
    uvicorn.run(
        app="main:app",
        port=8080,
        reload=True,
    )
