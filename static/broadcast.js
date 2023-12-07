let peer;
const socket_broadcaster = new WebSocket(`ws://${window.location.hostname}:8000/broadcast`);
console.log("This is ws: ", socket_broadcaster);

window.onload = () => {
    document.getElementById('my-button').onclick = () => {
        init();
    };
};

async function init() {
    console.log("button clicked");
    const stream = await navigator.mediaDevices.getUserMedia({ video: true });
    document.getElementById("video").srcObject = stream;
    peer = createPeer(); // Remove 'const' to use the global 'peer' variable
    stream.getTracks().forEach(track => peer.addTrack(track, stream));
}

function createPeer() {
    const peer = new RTCPeerConnection({});
    peer.onnegotiationneeded = () => handleNegotiationNeededEvent(peer);

    return peer;
}

async function handleNegotiationNeededEvent(peer) {
    const offer = await peer.createOffer();
    await peer.setLocalDescription(offer);
    const payload = peer.localDescription //this is a dict containing type and sdp as keys
    console.log(peer.localDescription);
    socket_broadcaster.send(JSON.stringify(payload));
}

socket_broadcaster.onmessage = function (event) {
    var message = event.data;
    try {
        var jsonMessage = JSON.parse(message);
        console.log("Message is: ", jsonMessage, "message.sdp is ", jsonMessage.sdp);
        const desc = new RTCSessionDescription(jsonMessage);
        peer.setRemoteDescription(desc).catch(e => console.log(e));
    } catch (e) {
        // If parsing as JSON fails, treat it as a text message
        console.log(e);
    }
};
