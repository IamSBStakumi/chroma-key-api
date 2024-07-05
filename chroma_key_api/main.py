from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

main = FastAPI()

origins = [
    "http://localhost:3000",
    "https://chroma-key-front-spbb34bsma-dt.a.run.app",
]

main.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["get", "post"],
    allow_headers=["*"]
)

# リクエストボディの型定義
class Param(BaseModel):
    contrast_adjustment_value: float
    chroma_key_color: list[int]
    chroma_key_threshold: int
    noise_removal_iterations: int

@main.get("/")
async def root():
    return {"message": "Hello World"}

@main.post("/create")
async def create_movie(param: Param):
    return {"message", f'{param.contrast_adjustment_value},{param.chroma_key_color},{param.chroma_key_threshold},{param.noise_removal_iterations}'}
