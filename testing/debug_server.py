from flask import Flask, request, jsonify
from servos import * 

app = Flask(__name__)

# ---- Pose library (edit to taste) ---------------------------------


crouch = {
        0: 180, 1: 0,  2: 0,
        4: 0,   5: 180,6: 180,
        8: 180, 9: 0,  10: 0,
        12: 0,  13: 180,14: 180,
    }
stand = {
    0: 120, 1: 90,  2: 60,
    8: 120, 9: 90, 10: 60,
    4: 60,  5: 90,  6: 120,
    12:60, 13: 90, 14: 120,
}
rise = {
    0: 120, 1: 140,  2: 120,
    4: 60,  5: 40,  6: 60,
    8: 120, 9: 140, 10: 120,
    12:60, 13: 40, 14: 60,
}

POSES = {
    "crouch": crouch,
    "stand": stand,
    "rise": rise
}

# ---- API -----------------------------------------------------------
@app.route("/api/state")
def get_state():
    return jsonify({"angles": angles, "targets": targets})

@app.route("/api/set", methods=["POST"])
def set_servo_targets():
    data = request.get_json()
    if not isinstance(data, dict):
        return jsonify({"error": "Invalid JSON"}), 400

    cleaned = {}
    for ch, ang in data.items():
        try:
            ch = int(ch)
            ang = int(ang)
            if ch in targets:
                cleaned[ch] = max(0, min(180, ang))
        except Exception:
            continue

    if not cleaned:
        return jsonify({"error": "No valid servo targets"}), 400

    set_targets(cleaned)
    return jsonify({"status": "ok", "new_targets": cleaned})

@app.route("/api/poses")
def list_poses():
    return jsonify(sorted(POSES.keys()))

@app.route("/api/pose/<name>", methods=["POST"])
def apply_pose(name):
    pose = POSES.get(name)
    if not pose:
        return jsonify({"error": f"Unknown pose '{name}'"}), 404
    set_targets(pose)
    return jsonify({"status": "ok", "pose": name})

@app.route("/api/kill", methods=["POST"])
def kill_servos():
    global ALIVE
    ALIVE = False
    try:
        kill()
    except Exception as e:
        print(f"[WARN] Kill failed: {e}")
    return jsonify({"status": "kill called"})

# ---- UI ------------------------------------------------------------
@app.route("/")
def index():
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body { font-family: sans-serif; background: #f9f9f9; padding: 2em; }
            .servo { margin-bottom: 1em; }
            input[type=range] { width: 280px; }
            h3 { margin: 0.6em 0; }
            button { margin: 0.25em 0.5em 0.25em 0; padding: 0.5em 1em; font-weight: 600; }
            .row { display: flex; gap: 80px; margin-top: 1.5em; }
            .col { flex: 1; }
        </style>
    </head>
    <body>
        <div id="poseButtons"></div>
        <button onclick="sendKill()">Kill All</button>

        <div class="row">
            <div class="col" id="FL"><h3>Front-Left (0,1,2)</h3></div>
            <div class="col" id="FR"><h3>Front-Right (4,5,6)</h3></div>
        </div>
        <div class="row">
            <div class="col" id="BL"><h3>Back-Left (8,9,10)</h3></div>
            <div class="col" id="BR"><h3>Back-Right (12,13,14)</h3></div>
        </div>

        <script>
            const layout = { FL:[0,1,2], FR:[4,5,6], BL:[8,9,10], BR:[12,13,14] };

            function createSliders() {
                for (const group in layout) {
                    const container = document.getElementById(group);
                    layout[group].forEach(ch => {
                        const div = document.createElement("div");
                        div.className = "servo";
                        div.innerHTML = `
                            <label>Channel ${ch}</label><br>
                            <input type="range" id="s${ch}" min="0" max="180" value="90"
                                   oninput="sendServo(${ch}, this.value)">
                            <span id="v${ch}">90</span>`;
                        container.appendChild(div);
                    });
                }
            }

            function loadPoseButtons() {
                fetch('/api/poses')
                  .then(r => r.json())
                  .then(names => {
                      const box = document.getElementById('poseButtons');
                      names.forEach(n => {
                          const b = document.createElement('button');
                          b.innerText = n;
                          b.onclick = () => fetch('/api/pose/' + n, {method:'POST'}).then(syncFromServer);
                          box.appendChild(b);
                      });
                  });
            }

            function sendServo(ch, val) {
                document.getElementById(`v${ch}`).innerText = val;
                fetch('/api/set', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({ [ch]: parseInt(val) })
                });
            }

            function sendKill() {
                fetch('/api/kill', { method: 'POST' }).then(syncFromServer);
            }

            function syncFromServer() {
                fetch('/api/state')
                  .then(res => res.json())
                  .then(data => {
                      for (const ch in data.targets) {
                          const slider = document.getElementById(`s${ch}`);
                          const label = document.getElementById(`v${ch}`);
                          if (slider && label) {
                              slider.value = data.targets[ch];
                              label.innerText = data.targets[ch];
                          }
                      }
                  });
            }

            createSliders();
            loadPoseButtons();
            syncFromServer();
        </script>
    </body>
    </html>
    """

if __name__ == "__main__":
    print("🚀 Servo Debug Server running at http://0.0.0.0:5000")
    app.run(host="0.0.0.0", port=5000, debug=False)
