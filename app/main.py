from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse

from app.database import init_db
from app.routers import entries_router, reports_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await init_db()
    yield
    # Shutdown


app = FastAPI(
    title="TinyLearn",
    description="每天一条学习记录，自动构建知识体系",
    version="0.1.0",
    lifespan=lifespan,
)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Templates
templates = Jinja2Templates(directory="templates")

# Include routers
app.include_router(entries_router)
app.include_router(reports_router)


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """首页 - 输入学习内容"""
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/review", response_class=HTMLResponse)
async def review(request: Request):
    """报告页面 - 查看知识体系和漏洞"""
    return templates.TemplateResponse("review.html", {"request": request})
