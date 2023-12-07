let peer;
const socket_listener = new WebSocket(`ws://localhost:8000/consumer`);
console.log("This is ws: ", socket_listener);

window.onload = () => {
    document.getElementById('my-button').onclick = () => {
        init();
    }
}

async function init() {
    const peer = createPeer();
    peer.addTransceiver("video", { direction: "recvonly" })
}

function createPeer() {
    const peer = new RTCPeerConnection({});
    peer.ontrack = handleTrackEvent;
    peer.onnegotiationneeded = () => handleNegotiationNeededEvent(peer);

    return peer;
}

async function handleNegotiationNeededEvent(peer) {
    const offer = await peer.createOffer();
    await peer.setLocalDescription(offer);
    const payload = peer.localDescription //this is a dict containing type and sdp as keys
    console.log(peer.localDescription);
    socket_listener.send(JSON.stringify(payload));
 }

function handleTrackEvent(e) {
    document.getElementById("video").srcObject = e.streams[0];
};

socket_listener.onmessage = function (event) {
    var message = event.data;
    try {
        var jsonMessage = JSON.parse(message);
        console.log("Message is: ", jsonMessage, "message.sdp is ", jsonMessage.sdp);
        console.log("Error didn't occur before we set the value of desc");
        const desc = new RTCSessionDescription(jsonMessage);
        console.log("Error didn't occur after we set the value of desc");
        peer.setRemoteDescription(desc).catch(e => console.log(e));
    } catch (e) {
        // If parsing as JSON fails, treat it as a text message
        console.log(e);
    }
};