from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from functions import ConnectionManager as cm
from functions import compose_movie
from functions import global_value as g

server = FastAPI()

origins = [
    "http://localhost:3000",
    "https://chroma-key-front-spbb34bsma-dt.a.run.app",
]

server.add_middleware(
    CORSMiddleware, allow_origins=origins, allow_credentials=True, allow_methods=["get", "post"], allow_headers=["*"]
)

ws_manager = cm.ConnectionManager()


@server.get("/")
async def root():
    return {"message": "Hello World"}


server.include_router(
    compose_movie.router,
)


@server.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await ws_manager.connect(websocket)
    try:
        while True:
            msg = await websocket.receive_text()
            await ws_manager.send_message({msg: "{:.3f}".format(g.val)})
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)


@server.exception_handler(RequestValidationError)
async def handler(request: Request, exc: RequestValidationError):
    print(exc)
    return JSONResponse(content={}, status_code=status.HTTP_422_UNPROCESSABLE_ENTITY)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(server, host="0.0.0.0", port=8080)
