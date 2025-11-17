from flask import Flask, render_template_string, jsonify, send_from_directory
import os

app = Flask(__name__)

# ====================== 상태 변수 ======================
reaction_count = 0
slide_index    = 1
history        = {}

# ====================== Presenter 페이지 ======================
#  - 전체 화면에 Google Slides embed
#  - 그 위에 🔥 이모티콘 레이어만 존재
PRESENTER_HTML = PRESENTER_HTML = PRESENTER_HTML = r"""
<!doctype html>
<html lang="ko">
<head>
  <meta charset="utf-8" />
  <title>Presenter View</title>
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <style>
    * { box-sizing:border-box; }
    html, body {
      margin:0;
      padding:0;
      width:100%;
      height:100%;
      background:#000;
      overflow:hidden;
      font-family: system-ui, -apple-system, Segoe UI, Roboto, sans-serif;
    }
    .root {
      position:relative;
      width:100%;
      height:100%;
      overflow:hidden;
    }
    /* 슬라이드 iframe: 화면 전체 채우기 */
    iframe {
      position:absolute;
      inset:0;
      width:100%;
      height:100%;
      border:0;
    }
    /* 이펙트 레이어 (iframe 위) */
    #emoji-layer {
      pointer-events:none;
      position:absolute;
      inset:0;
      overflow:hidden;
      z-index:10;
    }

    /* 메인 불꽃 이모티콘 */
    .emoji {
      position:absolute;
      font-size:48px;
      animation: riseUp var(--dur,1s) ease-out forwards;
      filter: drop-shadow(0 0 8px rgba(255,120,0,0.75));
    }

    /* 주변에 튀는 작은 불꽃 점들 */
    .spark {
      position:absolute;
      width:8px;
      height:8px;
      border-radius:999px;
      background: radial-gradient(circle at 30% 30%, #fff7d1 0, #ffc94a 35%, #ff6b00 100%);
      box-shadow:0 0 10px rgba(255,140,0,0.8);
      opacity:0.95;
      animation: sparkUp var(--dur,0.7s) ease-out forwards;
    }

    @keyframes riseUp {
      0%   { transform: translate3d(0,0,0) scale(1.0);   opacity:1; }
      60%  { transform: translate3d(0,-70px,0) scale(1.18); opacity:1; }
      100% { transform: translate3d(0,-120px,0) scale(0.9); opacity:0; }
    }

    /* 좌우로 살짝 흩어지며 위로 올라가는 스파크 */
    @keyframes sparkUp {
      0% {
        transform: translate3d(0,0,0) scale(1);
        opacity:0.95;
      }
      100% {
        transform: translate3d(var(--dx,0px), -60px, 0) scale(0.4);
        opacity:0;
      }
    }

    /* ===== 폭죽 파티클 (좀 더 크고 화려하게) ===== */
    .fw-spark {
      position:absolute;
      width:14px;
      height:14px;
      border-radius:999px;
      background: radial-gradient(circle at 30% 30%, #ffffff 0, var(--col,#ff6b6b) 40%, #000 100%);
      box-shadow:
        0 0 14px var(--col,rgba(255,255,255,0.9)),
        0 0 28px rgba(255,255,255,0.45);
      opacity:0.97;
      animation: fwOut var(--dur,1.1s) cubic-bezier(0.16, 0.64, 0.29, 0.99) forwards;
    }

    @keyframes fwOut {
      0% {
        transform: translate3d(0,0,0) scale(0.9);
        opacity:1;
      }
      60% {
        transform: translate3d(var(--dx,0px), var(--dy,-120px), 0) scale(1.1);
        opacity:1;
      }
      100% {
        transform: translate3d(calc(var(--dx,0px) * 1.2), calc(var(--dy,-120px) * 1.2 + 40px), 0) scale(0.4);
        opacity:0;
      }
    }
  </style>
</head>
<body>
  <div class="root">
    <!-- 정수 구글 슬라이드 embed (자동넘김 없음) -->
    <iframe
      src="https://docs.google.com/presentation/d/16CF0ulKWAy1S52Rrql8DJT1DSv2MyPlMhxN_6KE2nMY/embed?start=false&loop=false"
      allowfullscreen
    ></iframe>

    <!-- 🔥 이모티콘 + 파티클 레이어 -->
    <div id="emoji-layer"></div>
  </div>

  <script>
    const layer = document.getElementById('emoji-layer');
    let lastCount = 0;

    // 메인 불꽃 + 주변 스파크
    function spawnFire() {
      const vw = window.innerWidth;
      const vh = window.innerHeight;

      // 가로 20~80% 랜덤, 세로는 화면 아래쪽에서 시작
      const x = vw * 0.2 + Math.random() * vw * 0.6;
      const y = vh * 0.7;

      // 메인 🔥 이모티콘
      const flame = document.createElement('div');
      flame.className = 'emoji';
      flame.textContent = '🔥';
      flame.style.left = x + 'px';
      flame.style.top  = y + 'px';
      flame.style.setProperty('--dur', (0.85 + Math.random()*0.4) + 's');

      layer.appendChild(flame);
      flame.addEventListener('animationend', () => flame.remove());

      // 주변에 튀는 작은 스파크들 (3~5개)
      const sparkCount = 3 + Math.floor(Math.random()*3);
      for (let i = 0; i < sparkCount; i++) {
        const s = document.createElement('div');
        s.className = 'spark';

        // 시작 위치: 큰 불꽃 주변 약간 랜덤
        const offsetX = (Math.random() - 0.5) * 26;   // -13 ~ +13
        const offsetY = (Math.random() - 0.2) * 16;   // 살짝 위/아래

        s.style.left = (x + offsetX) + 'px';
        s.style.top  = (y + offsetY) + 'px';

        // 위로 올라가면서 좌우로 퍼지는 정도 & 속도 랜덤
        const dx = (Math.random() - 0.5) * 60; // -30 ~ +30
        const dur = 0.45 + Math.random()*0.35; // 0.45 ~ 0.8s
        s.style.setProperty('--dx', dx + 'px');
        s.style.setProperty('--dur', dur + 's');

        layer.appendChild(s);
        s.addEventListener('animationend', () => s.remove());
      }
    }

    // 3명 이상 동시에 👍 → 폭죽 (화면 랜덤 위치)
    function spawnFirework() {
      const vw = window.innerWidth;
      const vh = window.innerHeight;

      // 화면 전체를 쓰되, 가장자리 너무 붙지 않게 약간 여유
      const x = vw * (0.15 + Math.random()*0.7);  // 15% ~ 85%
      const y = vh * (0.20 + Math.random()*0.5);  // 20% ~ 70%

      const colors = ['#ff6b6b','#ffd93d','#4dd0e1','#7e57c2','#ff9f1a','#00e676'];
      const count = 22 + Math.floor(Math.random()*8); // 22~29개

      for (let i = 0; i < count; i++) {
        const p = document.createElement('div');
        p.className = 'fw-spark';

        // 각도를 고르게 분포시키되 약간 랜덤
        const angle = (Math.PI * 2 * i) / count + (Math.random()-0.5)*0.35;
        const radius = 110 + Math.random()*80; // 110~190px

        const dx = Math.cos(angle) * radius;
        const dy = Math.sin(angle) * radius;

        const col = colors[Math.floor(Math.random()*colors.length)];
        const dur = 0.8 + Math.random()*0.4;

        p.style.left = x + 'px';
        p.style.top  = y + 'px';
        p.style.setProperty('--dx', dx + 'px');
        p.style.setProperty('--dy', dy + 'px');
        p.style.setProperty('--dur', dur + 's');
        p.style.setProperty('--col', col);

        layer.appendChild(p);
        p.addEventListener('animationend', () => p.remove());
      }
    }

    async function refresh() {
      try {
        const r = await fetch('/count');
        const d = await r.json();
        const newCount = d.count ?? 0;

        const diff = newCount - lastCount;

        if (diff > 0) {
          // 👍 1번당 "불꽃 묶음" 5~6개
          for (let i = 0; i < diff; i++) {
            const burst = 5 + Math.floor(Math.random() * 2); // 5 또는 6
            for (let j = 0; j < burst; j++) {
              spawnFire();
            }
          }

          // 👥 diff가 3 이상이면 "동시에 3명 이상"으로 보고 폭죽 발사
          if (diff >= 3) {
            const fwTimes = diff >= 10 ? 2 : 1; // 너무 많으면 두 발
            for (let k = 0; k < fwTimes; k++) {
              spawnFirework();
            }
          }
        }

        lastCount = newCount;
      } catch (e) {
        console.warn('refresh error', e);
      }
    }

    // 좀 더 즉각적으로 보이게 0.2초마다 체크
    setInterval(refresh, 200);
  </script>
</body>
</html>
"""


# ====================== Audience 페이지 (기존 Mediapipe) ======================
AUDIENCE_HTML = r"""
<!doctype html>
<html lang="ko">
<head>
  <meta charset="utf-8" />
  <title>👍 Thumbs-Up Detector</title>
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <style>
    :root { color-scheme: dark; }
    body { margin: 0; font-family: system-ui, -apple-system, Segoe UI, Roboto, sans-serif; background:#0b0b0c; color:#eaeaea; }
    .wrap { display:flex; gap:16px; padding:16px; flex-wrap:wrap; }
    .panel { background:#141416; border-radius:14px; padding:12px; box-shadow:0 0 0 1px #232328 inset; }
    canvas, video { width: 46vw; max-width: 720px; aspect-ratio: 4/3; border-radius:12px; background:#0f0f11; }
    .right { min-width: 320px; flex: 1 1 340px; }
    .badge { background:#1f2026; padding:6px 10px; border-radius:999px; display:inline-flex; gap:8px; align-items:center; margin:4px 6px 0 0; }
    button { background:#2563eb; color:white; border:0; border-radius:10px; padding:10px 16px; font-weight:600; cursor:pointer; }
    button:disabled { opacity:.6; cursor:default; }
    .hint { color:#9aa0a6; font-size:14px; line-height:1.5; margin-top:10px; }
    .row { display:flex; gap:12px; margin-top:10px; align-items:center; }
    .err { color:#ff7a7a; }
    .ok { color:#7ddc7a; }
  </style>
</head>
<body>
  <div class="wrap">
    <div class="panel">
      <video id="video" playsinline muted style="display:none"></video>
      <canvas id="viewL"></canvas>
    </div>

    <div class="panel">
      <canvas id="viewR"></canvas>
    </div>

    <div class="panel right">
      <h2>👍 Thumbs-Up Detector (Only counts 👍)</h2>
      <div class="row">
        <div class="badge">Status <span id="status">Idle</span></div>
      </div>
      <div class="row">
        <div class="badge">Hands <span id="hands">0</span></div>
        <div class="badge">Sent <span id="sent">0</span></div>
      </div>
      <div class="row" style="margin-top:14px">
        <button id="start">🎥 START</button>
        <button id="test">Send test POST</button>
      </div>
      <p class="hint" id="warn"></p>
    </div>
  </div>

  <!-- =====================  MAIN SCRIPT  ===================== -->
  <script type="module">
  import {
    FilesetResolver,
    HandLandmarker,
    DrawingUtils
  } from "https://cdn.jsdelivr.net/npm/@mediapipe/tasks-vision@0.10.14";

  const statusEl = document.getElementById("status");
  const handsEl  = document.getElementById("hands");
  const sentEl   = document.getElementById("sent");
  const warnEl   = document.getElementById("warn");
  const video    = document.getElementById("video");
  const viewL    = document.getElementById("viewL");
  const viewR    = document.getElementById("viewR");
  const ctxL     = viewL.getContext("2d");
  const ctxR     = viewR.getContext("2d");
  const drawer   = new DrawingUtils(ctxR);

  // ---- 로컬 경로(Flask가 제공) ----
  const LOCAL_BASE = "/mp"; // 여기에서 wasm/js/task 3개를 가져옴

  let landmarker = null;
  let running = false;
  let sendCooldown = 0;
  let holdFrames   = 0;
  let sentCount    = 0;

  function status(t, cls=''){ statusEl.textContent = t; statusEl.className = cls; }
  function setHands(n){ handsEl.textContent = n; }
  function setSent(n){  sentEl.textContent  = n; }

  async function initModel(){
    status("Loading model…");
    const files = await FilesetResolver.forVisionTasks(LOCAL_BASE);
    landmarker = await HandLandmarker.createFromOptions(files, {
      baseOptions: { modelAssetPath: `${LOCAL_BASE}/hand_landmarker.task` },
      runningMode: "VIDEO",
      numHands: 4,
      minHandDetectionConfidence: 0.6,
      minHandPresenceConfidence: 0.6,
      minTrackingConfidence: 0.6,
    });
    status("Model ready", "ok");
  }

  function fitCanvases(){
    const w = video.videoWidth  || 640;
    const h = video.videoHeight || 480;
    if (viewL.width !== w){ viewL.width = w; viewR.width = w; }
    if (viewL.height!== h){ viewL.height= h; viewR.height= h; }
  }

  // 빠르고 보수적인 엄지척 판정 (엄지 끝이 다른 손가락/손목보다 위)
  function isThumbsUp(lm){
    if (!lm || lm.length < 21) return false;
    const wr  = lm[0];
    const t4  = lm[4];
    const i8  = lm[8], m12 = lm[12], r16 = lm[16], p20 = lm[20];
    return t4.y < wr.y && t4.y < i8.y && t4.y < m12.y && t4.y < r16.y && t4.y < p20.y;
  }

  function drawResults(results){
    ctxR.clearRect(0,0,viewR.width,viewR.height);
    if (!results || !results.landmarks){ setHands(0); return 0; }
    let up = 0;
    for (const lm of results.landmarks){
      drawer.drawLandmarks(lm, { radius: 1.6 });
      drawer.drawConnectors(lm, HandLandmarker.HAND_CONNECTIONS, { lineWidth: 1 });
      if (isThumbsUp(lm)) up++;
    }
    setHands(results.landmarks.length);
    return up;
  }

  async function sendReact(){
    try { await fetch("/react", { method:"POST" }); setSent(++sentCount); }
    catch(e){ console.warn("POST /react 실패", e); }
  }

  async function loop(){
    if (!running || !landmarker) return;
    try{
      fitCanvases();

      // 좌측: 미러 비디오
      ctxL.save();
      ctxL.scale(-1,1);
      ctxL.drawImage(video, -viewL.width, 0, viewL.width, viewL.height);
      ctxL.restore();

      const now = performance.now();
      const results = landmarker.detectForVideo(video, now);
      const ups = drawResults(results);

      if (ups > 0){
        holdFrames++;
        if (holdFrames >= 3 && sendCooldown === 0){
          sendCooldown = 10; // 10프레임 쿨다운
          holdFrames = 0;
          sendReact();
        }
      } else {
        holdFrames = 0;
        if (sendCooldown>0) sendCooldown--;
      }
    }catch(e){
      console.warn('detect error', e);
    }
    requestAnimationFrame(loop);
  }

  async function startCamera(){
    try{
      status("Requesting camera…");
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { width:{ideal:640}, height:{ideal:480}, frameRate:{ideal:15, max:24} },
        audio: false
      });
      video.srcObject = stream;
      await new Promise(res => video.onloadedmetadata = res);
      await video.play();
      status("Camera on", "ok");

      await initModel();

      running = true;
      status("Running (raise 👍)", "ok");
      loop();
    }catch(e){
      const msg = (e && (e.message || e.name)) ? e.message || e.name : String(e);
      let human = '카메라 시작 실패. ';
      const lower = msg.toLowerCase();
      if (lower.includes('notallowed') || lower.includes('permission')) human += '브라우저 주소창 카메라 권한을 허용해 주세요.';
      else if (lower.includes('notfound') || lower.includes('device')) human += '사용 가능한 카메라가 없거나 다른 앱이 점유 중입니다(Zoom/Meet/OBS 종료).';
      else human += msg;
      status(human, 'err');
      throw e;
    }
  }

  document.getElementById("start").onclick = async (ev)=>{
    const btn = ev.currentTarget;
    btn.disabled = true;
    try { await startCamera(); btn.remove(); }
    catch(e){ btn.disabled = false; }
  };

  document.getElementById("test").onclick = ()=> sendReact();

  if (location.protocol !== "https:" && location.hostname !== "localhost") {
    warnEl.textContent = "⚠️ HTTPS 링크로 접속해야 카메라 접근이 가능해요.";
  }

  // 필수 파일이 있는지 빠르게 확인해서 없으면 안내
  fetch('/mp/check').then(r=>r.json()).then(j=>{
    const miss = Object.entries(j).filter(([k,v])=>!v).map(([k])=>k);
    if (miss.length){
      warnEl.innerHTML = "❌ 필수 파일 누락: <b>" + miss.join(', ') + "</b><br>static/mp 폴더에 3개 파일(vision_wasm_internal.js, vision_wasm_internal.wasm, hand_landmarker.task)을 넣으세요.";
      status("Missing files", "err");
      document.getElementById('start').disabled = true;
    }
  }).catch(()=>{});
  </script>
</body>
</html>
"""

# ====================== Routes ======================

@app.route("/")
def presenter():
  return render_template_string(PRESENTER_HTML, slide=slide_index)

@app.route("/audience")
def audience():
  return render_template_string(AUDIENCE_HTML)

# Mediapipe wasm/모델 파일 제공
@app.route("/mp/<path:filename>")
def mp_files(filename):
  return send_from_directory("static/mp", filename)

# 필수 파일 존재 여부 확인 (클라이언트에서 안내용)
@app.route("/mp/check")
def mp_check():
  base = os.path.join(app.root_path, "static", "mp")
  files = {
      "vision_wasm_internal.js": os.path.exists(os.path.join(base, "vision_wasm_internal.js")),
      "vision_wasm_internal.wasm": os.path.exists(os.path.join(base, "vision_wasm_internal.wasm")),
      "hand_landmarker.task": os.path.exists(os.path.join(base, "hand_landmarker.task")),
  }
  return jsonify(files)

@app.route("/react", methods=["POST"])
def react():
  global reaction_count
  reaction_count += 1
  return "", 204

@app.route("/count")
def count():
  return jsonify({"count": reaction_count, "slide": slide_index})

@app.route("/next", methods=["POST"])
def next_slide():
  global reaction_count, slide_index, history
  history[slide_index] = reaction_count
  slide_index += 1
  reaction_count = 0
  return "", 204

@app.route("/summary")
def summary():
  return jsonify(history)

# 카메라 단독 테스트 (권한/점유 문제 빠르게 확인)
@app.route("/camtest")
def camtest():
  return render_template_string("""
  <video id="v" playsinline autoplay muted style="width:80vw;max-width:900px;background:#000"></video>
  <pre id="e" style="white-space:pre-wrap;"></pre>
  <script>
    (async()=>{
      try{
        const s=await navigator.mediaDevices.getUserMedia({video:true,audio:false});
        v.srcObject=s; await v.play();
      }catch(err){ e.textContent = String(err && (err.message||err.name) || err); }
    })();
  </script>
  """)

# ====================== 실행 ======================
if __name__ == "__main__":
  print("✅ Presenter : http://localhost:8000")
  print("✅ Audience  : http://localhost:8000/audience")
  app.run(host="0.0.0.0", port=8000, debug=False)



