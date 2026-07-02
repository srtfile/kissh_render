import requests
from urllib.parse import quote
from flask import Flask, render_template_string, request, jsonify

app = Flask(__name__)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36",
    "Accept": "application/json"
}

API = "https://enc-dec.app/api"

HTML = '''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>KissKH Extractor</title>
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body { font-family: 'Segoe UI', sans-serif; background: #0f0f1a; color: #e0e0e0; min-height: 100vh; padding: 20px; }
  .container { max-width: 900px; margin: 0 auto; }
  h1 { text-align: center; color: #e91e8c; margin-bottom: 8px; font-size: 2rem; }
  .subtitle { text-align: center; color: #888; margin-bottom: 30px; font-size: 0.9rem; }
  .card { background: #1a1a2e; border: 1px solid #2a2a4a; border-radius: 12px; padding: 24px; margin-bottom: 20px; }
  label { display: block; margin-bottom: 6px; color: #aaa; font-size: 0.85rem; text-transform: uppercase; letter-spacing: 0.05em; }
  input { width: 100%; padding: 10px 14px; background: #0f0f1a; border: 1px solid #3a3a5a; border-radius: 8px; color: #e0e0e0; font-size: 0.95rem; margin-bottom: 16px; outline: none; }
  input:focus { border-color: #e91e8c; }
  button { width: 100%; padding: 12px; background: #e91e8c; color: white; border: none; border-radius: 8px; font-size: 1rem; font-weight: 600; cursor: pointer; transition: background 0.2s; }
  button:hover { background: #c2185b; }
  button:disabled { background: #444; cursor: not-allowed; }
  .output { background: #0a0a15; border: 1px solid #2a2a4a; border-radius: 8px; padding: 16px; min-height: 120px; font-family: monospace; font-size: 0.85rem; white-space: pre-wrap; word-break: break-all; color: #a0f0a0; }
  .output-sub { background: #0a0a15; border: 1px solid #2a2a4a; border-radius: 8px; padding: 16px; min-height: 60px; font-family: monospace; font-size: 0.85rem; white-space: pre-wrap; word-break: break-all; color: #f0d0a0; margin-top: 12px; }
  .step { display: flex; align-items: center; gap: 10px; padding: 8px 0; border-bottom: 1px solid #2a2a4a; color: #888; font-size: 0.85rem; }
  .step:last-child { border-bottom: none; }
  .dot { width: 8px; height: 8px; border-radius: 50%; background: #444; flex-shrink: 0; }
  .step.done .dot { background: #4caf50; }
  .step.active .dot { background: #e91e8c; animation: pulse 1s infinite; }
  .step.error .dot { background: #f44336; }
  @keyframes pulse { 0%,100%{opacity:1} 50%{opacity:0.3} }
  .badge { display: inline-block; padding: 2px 8px; border-radius: 4px; font-size: 0.75rem; background: #2a2a4a; color: #e91e8c; margin-left: 8px; }
  .error-msg { color: #f44336; }
</style>
</head>
<body>
<div class="container">
  <h1>💋 KissKH</h1>
  <p class="subtitle">Extract stream & subtitle data from kisskh.do</p>
  <div class="card">
    <label>Content ID (Episode ID)</label>
    <input type="text" id="content_id" value="192143" placeholder="e.g. 192143">
    <button id="runBtn" onclick="run()">▶ Extract Stream & Subtitles</button>
  </div>
  <div class="card">
    <label>Progress</label>
    <div id="steps">
      <div class="step" id="s1"><div class="dot"></div> Get Video Key & Stream</div>
      <div class="step" id="s2"><div class="dot"></div> Get Subtitle Key & List</div>
      <div class="step" id="s3"><div class="dot"></div> Decrypt First Subtitle</div>
    </div>
  </div>
  <div class="card">
    <label>Video Response <span class="badge" id="badge"></span></label>
    <div class="output" id="output">Results will appear here...</div>
    <label style="margin-top:16px;">Subtitles</label>
    <div class="output" id="output_sub">Subtitle data will appear here...</div>
    <label style="margin-top:16px;">Decrypted Subtitle Preview</label>
    <div class="output-sub" id="output_dec">Decrypted subtitle will appear here...</div>
  </div>
</div>
<script>
async function run() {
  const btn = document.getElementById('runBtn');
  btn.disabled = true;
  ['output','output_sub','output_dec'].forEach(id => document.getElementById(id).textContent = 'Running...');
  document.getElementById('badge').textContent = '';
  ['s1','s2','s3'].forEach(id => document.getElementById(id).className = 'step');
  try {
    const resp = await fetch('/run', {
      method: 'POST',
      headers: {'Content-Type':'application/json'},
      body: JSON.stringify({ content_id: document.getElementById('content_id').value })
    });
    const data = await resp.json();
    data.steps.forEach((s,i) => document.getElementById('s'+(i+1)).classList.add(s.status));
    if (data.error) {
      document.getElementById('output').innerHTML = '<span class="error-msg">ERROR: ' + data.error + '</span>';
      document.getElementById('badge').textContent = 'FAILED';
    } else {
      document.getElementById('output').textContent = JSON.stringify(data.video, null, 2);
      document.getElementById('output_sub').textContent = JSON.stringify(data.subtitles, null, 2);
      document.getElementById('output_dec').textContent = data.decrypted_sub || '(no subtitle)';
      document.getElementById('badge').textContent = 'SUCCESS';
    }
  } catch(e) {
    document.getElementById('output').innerHTML = '<span class="error-msg">' + e.message + '</span>';
  }
  btn.disabled = false;
}
</script>
</body>
</html>'''

@app.route('/')
def index():
    return render_template_string(HTML)

@app.route('/run', methods=['POST'])
def run():
    content_id = request.json.get('content_id', '')
    steps = [{"status": "active"}, {"status": ""}, {"status": ""}]
    try:
        enc_vid = requests.get(f"{API}/enc-kisskh?text={content_id}&type=vid", timeout=10).json()
        if enc_vid.get("status") != 200:
            steps[0]["status"] = "error"
            return jsonify({"steps": steps, "error": enc_vid.get("error", "vid key failed")})
        vid_key = enc_vid["result"]
        video_resp = requests.get(f"https://kisskh.do/api/DramaList/Episode/{content_id}.png?err=false&ts=&time=&kkey={vid_key}", headers=HEADERS, timeout=15).json()
        steps[0]["status"] = "done"

        steps[1]["status"] = "active"
        enc_sub = requests.get(f"{API}/enc-kisskh?text={content_id}&type=sub", timeout=10).json()
        if enc_sub.get("status") != 200:
            steps[1]["status"] = "error"
            return jsonify({"steps": steps, "error": enc_sub.get("error", "sub key failed"), "video": video_resp})
        sub_key = enc_sub["result"]
        sub_resp = requests.get(f"https://kisskh.do/api/Sub/{content_id}?kkey={sub_key}", headers=HEADERS, timeout=15).json()
        steps[1]["status"] = "done"

        steps[2]["status"] = "active"
        decrypted_sub = ""
        if sub_resp and len(sub_resp) > 0:
            subtitle_url = sub_resp[0].get('src', '')
            if subtitle_url:
                dec_text = requests.get(f"{API}/dec-kisskh?url={quote(subtitle_url)}", timeout=10).text
                decrypted_sub = dec_text[:500]
        steps[2]["status"] = "done"

        return jsonify({"steps": steps, "video": video_resp, "subtitles": sub_resp, "decrypted_sub": decrypted_sub})
    except Exception as e:
        for s in steps:
            if s["status"] == "active":
                s["status"] = "error"
        return jsonify({"steps": steps, "error": str(e)})

if __name__ == '__main__':
    import os
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
