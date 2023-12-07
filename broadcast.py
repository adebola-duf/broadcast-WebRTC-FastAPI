from fastapi import FastAPI, HTTPException, WebSocket, Request, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from aiortc import RTCPeerConnection, RTCSessionDescription, VideoStreamTrack, MediaStreamTrack
import json

app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("combined.html", {"request": request})


@app.websocket("/viewer")
async def consumer(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            params = await websocket.receive_json()

            pc = RTCPeerConnection()
            offer = RTCSessionDescription(
                sdp=params["sdp"], type=params["type"])

            await pc.setRemoteDescription(offer)
            if not sender_stream:
                raise HTTPException(
                    status_code=400, detail="No sender stream available")
            print(sender_stream)
            pc.addTrack(sender_stream)

            answer = await pc.createAnswer()
            await pc.setLocalDescription(answer)

            await websocket.send_json({"sdp": pc.localDescription.sdp, "type": pc.localDescription.type})
    except WebSocketDisconnect:
        pass

sender_stream: MediaStreamTrack | None = None


async def handle_media_stream(stream: MediaStreamTrack):
    global sender_stream
    sender_stream = stream


@app.websocket("/broadcast")
async def broadcast(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            params = await websocket.receive_text()
            params = json.loads(params)

            pc = RTCPeerConnection()
            pc.on("track", handle_media_stream)

            offer = RTCSessionDescription(**params)
            await pc.setRemoteDescription(offer)
            answer = await pc.createAnswer()
            await pc.setLocalDescription(answer)

            await websocket.send_json({"sdp": pc.localDescription.sdp, "type": pc.localDescription.type})
    except WebSocketDisconnect:
        pass
