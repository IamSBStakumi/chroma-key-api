from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn

server = FastAPI()

origins = [
    "http://localhost:3000",
    "https://chroma-key-front-spbb34bsma-dt.a.run.app",
]

server.add_middleware(
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

@server.get("/")
async def root():
    return {"message": "Hello World"}

@server.post("/create")
async def create_movie(param: Param):
    return {"message", f'{param.contrast_adjustment_value},{param.chroma_key_color},{param.chroma_key_threshold},{param.noise_removal_iterations}'}

if __name__ == "__main__":
    uvicorn.run(server, host="0.0.0.0", port=8080, log_level="debug")