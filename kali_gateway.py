from flask import Flask, render_template
import socket, struct, threading, cv2, numpy as np
from datetime import datetime
import os

app = Flask(__name__)

events = []   # store last 20
LOG_IMG_DIR = "static/captures"
os.makedirs(LOG_IMG_DIR, exist_ok=True)


def recv_exact(conn, size):
    data = b""
    while len(data) < size:
        packet = conn.recv(size - len(data))
        if not packet:
            return None
        data += packet
    return data


def tcp_listener():
    global events
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(('0.0.0.0', 9999))
    s.listen(5)

    print("[TCP] Listening on port 9999...")

    while True:
        conn, addr = s.accept()
        print(f"[TCP] Connected: {addr}")

        try:
            while True:
                # --- Metadata ---
                raw_len = recv_exact(conn, 4)
                if not raw_len:
                    break
                meta_len = struct.unpack('!I', raw_len)[0]
                metadata = recv_exact(conn, meta_len).decode()

                name, status, timestamp = metadata.split("|")

                # --- Image ---
                raw_len = recv_exact(conn, 4)
                frame_len = struct.unpack('!I', raw_len)[0]
                frame_data = recv_exact(conn, frame_len)

                np_frame = np.frombuffer(frame_data, dtype=np.uint8)
                frame = cv2.imdecode(np_frame, cv2.IMREAD_COLOR)

                filename = f"{datetime.now().strftime('%H%M%S')}.jpg"
                img_path = os.path.join(LOG_IMG_DIR, filename)
                cv2.imwrite(img_path, frame)

                event = {
                    "name": name,
                    "status": status,
                    "time": timestamp,
                    "image": f"captures/{filename}"
                }

                events.append(event)
                if len(events) > 20:
                    events.pop(0)

        except Exception as e:
            print("[TCP] Error:", e)

        conn.close()


threading.Thread(target=tcp_listener, daemon=True).start()


@app.route('/')
def index():
    total = len(events)
    granted = sum(1 for e in events if e["status"] == "GRANTED")
    denied = sum(1 for e in events if e["status"] == "DENIED")

    return render_template(
        'index.html',
        events=events,
        total=total,
        granted=granted,
        denied=denied
    )


app.run(host='0.0.0.0', port=5000)

