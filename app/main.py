from fastapi import Depends, FastAPI, Response, Security
from prometheus_fastapi_instrumentator import Instrumentator
from slowapi.middleware import SlowAPIASGIMiddleware

from app.endpoints import audio, chat, chunks, collections, completions, documents, embeddings, files, models, rerank, search
from app.helpers import MetricsMiddleware
from app.schemas.security import User
from app.utils.lifespan import lifespan
from app.utils.logging import logger
from app.utils.security import check_admin_api_key, check_api_key
from app.utils.settings import settings

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description=settings.app_description,
    contact={"url": settings.app_contact_url, "email": settings.app_contact_email},
    licence_info={"name": "MIT License", "identifier": "MIT"},
    lifespan=lifespan,
    docs_url="/swagger",
    redoc_url="/documentation",
)


@app.get("/")
async def root():
    logger.info("Accès à la route principale")
    return {"message": "Hello World"}


# Prometheus metrics
app.instrumentator = Instrumentator().instrument(app=app)

# Middlewares
app.add_middleware(middleware_class=SlowAPIASGIMiddleware)
app.add_middleware(middleware_class=MetricsMiddleware)


# Monitoring
@app.get(path="/health", tags=["Monitoring"])
def health(user: User = Security(dependency=check_api_key)) -> Response:
    """
    Health check.
    """

    return Response(status_code=200)


app.instrumentator.expose(app=app, should_gzip=True, tags=["Monitoring"], dependencies=[Depends(dependency=check_admin_api_key)])

# Core
app.include_router(router=models.router, tags=["Core"], prefix="/v1")
app.include_router(router=chat.router, tags=["Core"], prefix="/v1")
app.include_router(router=completions.router, tags=["Core"], prefix="/v1")
app.include_router(router=embeddings.router, tags=["Core"], prefix="/v1")
app.include_router(router=audio.router, tags=["Core"], prefix="/v1")
app.include_router(router=rerank.router, tags=["Core"], prefix="/v1")

# RAG
app.include_router(router=search.router, tags=["Retrieval Augmented Generation"], prefix="/v1")
app.include_router(router=collections.router, tags=["Retrieval Augmented Generation"], prefix="/v1")
app.include_router(router=files.router, tags=["Retrieval Augmented Generation"], prefix="/v1")
app.include_router(router=documents.router, tags=["Retrieval Augmented Generation"], prefix="/v1")
app.include_router(router=chunks.router, tags=["Retrieval Augmented Generation"], prefix="/v1")
