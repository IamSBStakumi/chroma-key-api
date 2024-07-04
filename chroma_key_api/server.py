from fastapi import FastAPI
import uvicorn

server = FastAPI()

@server.get("/")
async def root():
    return {"message": "Hello World"}

if __name__ == "__main__":
    uvicorn.run(server, host="0.0.0.0", port=8080, log_level="debug")