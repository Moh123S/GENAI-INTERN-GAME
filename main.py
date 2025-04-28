from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.routes import router
from core.rate_limiter import RateLimiter
import redis.asyncio as redis
from contextlib import asynccontextmanager
import asyncpg

app = FastAPI(title="What Beats Rock")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
redis_client = redis.Redis(host="redis", port=6379, decode_responses=True)

@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.redis = redis_client
    app.state.db = await asyncpg.create_pool(
        host="postgres", port=5432, database="game", user="user", password="password",
        min_size=5, max_size=20
    )
    yield
    await app.state.redis.aclose()
    await app.state.db.close()

app.router.lifespan = lifespan
app.include_router(router, prefix="/api")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)