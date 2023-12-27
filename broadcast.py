from fastapi import FastAPI, HTTPException, WebSocket, Request, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from aiortc import RTCPeerConnection, RTCSessionDescription, RTCConfiguration, MediaStreamTrack, RTCIceServer, RTCIceCandidate, RTCIceGatherer
import json
from dotenv import load_dotenv
import os

load_dotenv(".env")
turn_server_username = os.getenv("TURN_SERVER_USERNAME")
turn_server_password = os.getenv("TURN_SERVER_PASSWORD")
turn_servers: list[RTCIceServer] = [
    RTCIceServer(
        urls="stun:stun.relay.metered.ca:80"),
    RTCIceServer(
        urls=["turn:a.relay.metered.ca:80"],
        username=turn_server_username,
        credential=turn_server_password,
    ),
    RTCIceServer(
        urls=["turn:a.relay.metered.ca:80?transport=tcp"],
        username=turn_server_username,
        credential=turn_server_password,
    ),
    RTCIceServer(
        urls=["turn:a.relay.metered.ca:443"],
        username=turn_server_username,
        credential=turn_server_password,
    ),
    RTCIceServer(
        urls=["turn:a.relay.metered.ca:443?transport=tcp"],
        username=turn_server_username,
        credential=turn_server_username,
    ),
]

# Configure the RTCPeerConnection
configuration = RTCConfiguration(iceServers=turn_servers)

app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("combined.html", {"request": request})


def rtc_ice_candidate_arguments(candidate: dict):
    """Breaks the candidate into their individual components"""

    sdp_a_line = candidate["candidate"]
    sdp_a_line = sdp_a_line.split(" ")
    foundation: str = sdp_a_line[0].split(":")[1]
    component: int = int(sdp_a_line[1])
    ip: str = sdp_a_line[4]
    port: int = int(sdp_a_line[5])
    priority: int = int(sdp_a_line[3])
    protocol: str = sdp_a_line[2]
    type: str = sdp_a_line[7]
    sdpMid = candidate["sdpMid"]
    sdpMLineIndex = candidate["sdpMLineIndex"]
    return {"component": component, "foundation": foundation, "ip": ip, "port": port, "priority": priority, "protocol": protocol, "type": type, "sdpMid": sdpMid, "sdpMLineIndex": sdpMLineIndex}


@app.websocket("/viewer")
async def consumer(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_json()
            # print("viewer message:", data)
            data_content = data["data"]

            if data_content["type"] == "offer":
                pc = RTCPeerConnection(configuration=configuration)
                offer = RTCSessionDescription(**data_content)

                await pc.setRemoteDescription(offer)

                if not sender_stream:
                    raise HTTPException(
                        status_code=400, detail="No sender stream available")
                print(f"sender stream is: {sender_stream}")
                pc.addTrack(sender_stream)

                answer = await pc.createAnswer()
                await pc.setLocalDescription(answer)
                payload = {"data": {"sdp": pc.localDescription.sdp, "type": pc.localDescription.type}}
                await websocket.send_json(payload)
            elif data_content["type"] == "candidate":
                await pc.addIceCandidate(RTCIceCandidate(**rtc_ice_candidate_arguments(data_content["candidate"])))
                print("candidate added")
    except WebSocketDisconnect:
        pass

sender_stream: MediaStreamTrack | None = None


async def handle_media_stream(stream: MediaStreamTrack):
    global sender_stream
    sender_stream = stream

# this is to simulte the client the broadcaster is connecting 2 so this is pretty much the viewer
@app.websocket("/broadcast")
async def broadcast(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_json()
            # print("broadcaster message:", data)
            data_content = data["data"]
            # Create the RTCPeerConnection
            if data_content["type"] == "offer":
                pc = RTCPeerConnection(configuration=configuration)

                pc.on("track", handle_media_stream)
                pc.addTransceiver(trackOrKind="video", direction="recvonly")
                pc.addTransceiver(trackOrKind="audio", direction="recvonly")
            
                # pc.on
                offer = RTCSessionDescription(**data_content)
                await pc.setRemoteDescription(offer)
                answer = await pc.createAnswer()
                await pc.setLocalDescription(answer)
               
                payload = {"data": {"sdp": pc.localDescription.sdp, "type": pc.localDescription.type}}
                await websocket.send_json(payload)
            # BAd logic. what if pc is not created before they send canidate
            elif data_content["type"] == "candidate":
                await pc.addIceCandidate(RTCIceCandidate(**rtc_ice_candidate_arguments(data_content["candidate"])))
                print("candidate added")
                await RTCIceGatherer(iceServers=turn_servers).gather()
    except WebSocketDisconnect:
        pass
