#!/usr/bin/env python3
"""
MVP 服务启动器
快速启动 FastAPI 服务用于测试
"""

import uvicorn
import sys
import os

# 添加路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# 创建简化的 FastAPI 应用
app = FastAPI(
    title="InfraWatch MVP API",
    version="0.1.0",
)

# CORS - 允许所有来源
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 导入数据路由
from app.api.v1.data import router as data_router
from app.api.v1.supply_chain import router as supply_chain_router
from app.api.v1.signals import router as signals_router
from app.api.v1.stage import router as stage_router

app.include_router(data_router, prefix="/api/v1")
app.include_router(supply_chain_router, prefix="/api/v1")
app.include_router(signals_router, prefix="/api/v1")
app.include_router(stage_router, prefix="/api/v1")


@app.get("/")
async def root():
    return {
        "name": "InfraWatch MVP",
        "version": "0.1.0",
        "endpoints": {
            "prices": "/api/v1/data/prices",
            "metrics": "/api/v1/data/metrics",
            "summary": "/api/v1/data/summary",
        }
    }


@app.get("/health")
async def health():
    return {"status": "ok"}


if __name__ == "__main__":
    print("=" * 50)
    print("启动 InfraWatch MVP API")
    print("=" * 50)
    print("API 地址: http://localhost:8000")
    print("文档地址: http://localhost:8000/docs")
    print("=" * 50)
    
    uvicorn.run(
        "run_mvp:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )
