let peer, role;
let BroadcasterSocket = new WebSocket(`wss://${window.location.hostname}/broadcast`);
let viewersSocket = new WebSocket(`wss://${window.location.hostname}/viewer`);

// let BroadcasterSocket = new WebSocket(`ws://${window.location.hostname}:8000/broadcast`);
// let viewersSocket = new WebSocket(`ws://${window.location.hostname}:8000/viewer`);

var peerConfiguration = {};

(async() => {
  const response = await fetch("https://first-webrtc-app.metered.live/api/v1/turn/credentials?apiKey=df1e4b6b881387c5fb86162344907946ce62");
  const iceServers = response.data;
  peerConfiguration.iceServers = iceServers
})();

window.onload = () => {
    const buttons = document.querySelectorAll("button");
    buttons.forEach(button => {
        button.addEventListener("click", () => {
            role = button.id.split("-")[1];
            document.getElementById("role").textContent = role;
            init();
        });
    });
};

async function init() {
    if (role === "broadcaster") {
        console.log("Starting Broadcast...");
        const stream = await navigator.mediaDevices.getUserMedia({ video: true, audio: true });
        document.getElementById("video").srcObject = stream;
        peer = createPeer();
        stream.getTracks().forEach(track => peer.addTrack(track, stream));
    } else if (role === "viewer") {
        console.log("Connecting to Broadcaster...");
        peer = createPeer();
        peer.addTransceiver("video", { direction: "recvonly" });
    }
}

function createPeer() {
    peer = new RTCPeerConnection(peerConfiguration);
    if (role === "broadcaster")
        peer.onnegotiationneeded = () => handleNegotiationNeededEvent(peer);
    else if (role === "viewer"){
        peer.ontrack = handleTrackEvent;
        peer.onnegotiationneeded = () => handleNegotiationNeededEvent(peer);
    }
    return peer;
}

async function handleNegotiationNeededEvent(peer) {
    if (role === "broadcaster") {
        const offer = await peer.createOffer();
        await peer.setLocalDescription(offer);
        const payload = peer.localDescription //this is a dict containing type and sdp as keys
        console.log(peer.localDescription);
        BroadcasterSocket.send(JSON.stringify(payload));
    } else if (role === "viewer") {
        console.log("Creating Offer...");
        const offer = await peer.createOffer();
        await peer.setLocalDescription(offer);
        const payload = peer.localDescription //this is a dict containing type and sdp as keys
        console.log(peer.localDescription);
        viewersSocket.send(JSON.stringify(payload));
    }
}

function handleTrackEvent(e) {
  
        console.log("Adding Remote Track...");
        document.getElementById("video").srcObject = e.streams[0];
        console.log("track added");
  
};

BroadcasterSocket.onmessage = function (event) {
    try {
        var jsonMessage = JSON.parse(event.data);
        console.log("Broadcaster Message: ", jsonMessage);
        const desc = new RTCSessionDescription(jsonMessage);
        peer.setRemoteDescription(desc).catch(e => console.log(e));
    } catch (e) {
        console.error(e);
    }
};

viewersSocket.onmessage = function (event) {
    try {
        var jsonMessage = JSON.parse(event.data);
        console.log("Viewer Message: ", jsonMessage);
        const desc = new RTCSessionDescription(jsonMessage);
        peer.setRemoteDescription(desc).catch(e => console.log(e));
    } catch (e) {
        console.error(e);
    }
};