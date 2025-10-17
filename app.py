# # app.py
# # Hugging Face Space: LLM App Deployer API using Gradio
# # It receives a JSON request, validates secret, generates web app files,
# # creates a public GitHub repository, enables GitHub Pages, and notifies evaluation URL.

# import os
# import json
# import base64
# import time
# import uuid
# import traceback
# import requests
# import gradio as gr

# # ======== CONFIG FROM SECRETS ========
# GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")     # from Hugging Face Space Secrets
# SECRET_KEY = os.getenv("SECRET_KEY")         # from Hugging Face Space Secrets
# HF_TOKEN = os.getenv("HF_TOKEN", "")         # optional (for HF inference)
# AUTHOR = os.getenv("AUTHOR", "student")      # optional
# GITHUB_API = "https://api.github.com"

# # ==========================================================
# # Utility helpers
# # ==========================================================
# def log(msg: str):
#     print("[LOG]", msg, flush=True)


# def gh_headers():
#     if not GITHUB_TOKEN:
#         raise RuntimeError("Missing GITHUB_TOKEN secret")
#     return {
#         "Authorization": f"token {GITHUB_TOKEN}",
#         "Accept": "application/vnd.github.v3+json"
#     }


# def create_repo(name: str, desc: str):
#     """Create new public GitHub repo under authenticated user"""
#     payload = {"name": name, "description": desc, "auto_init": True, "private": False}
#     r = requests.post(f"{GITHUB_API}/user/repos", headers=gh_headers(), json=payload)
#     if r.status_code >= 300:
#         raise RuntimeError(f"GitHub repo create failed: {r.status_code} {r.text}")
#     return r.json()


# # def upload_file(owner: str, repo: str, path: str, content: str, message: str):
# #     """Upload file content to repo"""
# #     url = f"{GITHUB_API}/repos/{owner}/{repo}/contents/{path}"
# #     data = {
# #         "message": message,
# #         "content": base64.b64encode(content.encode()).decode()
# #     }
# #     r = requests.put(url, headers=gh_headers(), json=data)
# #     if r.status_code >= 300:
# #         raise RuntimeError(f"Upload {path} failed: {r.status_code} {r.text}")

# def upload_file(owner: str, repo: str, path: str, content: str, message: str):
#     """Create or update a file in the GitHub repo"""
#     url = f"{GITHUB_API}/repos/{owner}/{repo}/contents/{path}"
#     b64 = base64.b64encode(content.encode()).decode()

#     # Check if file exists
#     r = requests.get(url, headers=gh_headers())
#     if r.status_code == 200:
#         sha = r.json()["sha"]
#         payload = {"message": message, "content": b64, "sha": sha}
#     else:
#         payload = {"message": message, "content": b64}

#     r = requests.put(url, headers=gh_headers(), json=payload)
#     if r.status_code >= 300:
#         raise RuntimeError(f"Upload {path} failed: {r.status_code} {r.text}")



# def enable_pages(owner: str, repo: str):
#     """Enable GitHub Pages"""
#     url = f"{GITHUB_API}/repos/{owner}/{repo}/pages"
#     payload = {"source": {"branch": "main", "path": "/"}}
#     r = requests.post(url, headers=gh_headers(), json=payload)
#     if r.status_code >= 300:
#         requests.put(url, headers=gh_headers(), json=payload)  # fallback


# def latest_commit(owner: str, repo: str):
#     """Get latest commit SHA"""
#     r = requests.get(f"{GITHUB_API}/repos/{owner}/{repo}/commits", headers=gh_headers())
#     if r.status_code >= 300:
#         return "unknown"
#     return r.json()[0]["sha"]


# # ==========================================================
# # Web app file generator
# # ==========================================================
# def generate_files(brief: str):
#     """Return dictionary of filename→content for index.html, script.js, style.css"""
#     html = f"""<!DOCTYPE html>
# <html>
# <head>
#   <meta charset="utf-8">
#   <title>Generated App</title>
#   <meta name="viewport" content="width=device-width,initial-scale=1">
#   <link rel="stylesheet" href="style.css">
# </head>
# <body>
#   <main>
#     <h1>Generated Web App</h1>
#     <p>{brief}</p>
#     <div id="result">Click the button to show message</div>
#     <button onclick="showMessage()">Click Me</button>
#   </main>
#   <script src="script.js"></script>
# </body>
# </html>"""

#     js = """function showMessage(){
#   const el=document.getElementById('result');
#   el.textContent='This simple app works! Time: '+new Date().toLocaleString();
# }"""

#     css = """body{font-family:Arial;background:#eef5db;color:#333;text-align:center;margin-top:5%;}
# button{padding:10px 20px;font-size:16px;background:#4f6367;color:white;border:none;border-radius:8px;cursor:pointer;}
# button:hover{background:#7a9e9f;}"""

#     return {"index.html": html, "script.js": js, "style.css": css}


# # ==========================================================
# # Main handler for JSON input
# # ==========================================================
# def deploy(json_input: str):
#     try:
#         data = json.loads(json_input)
#         log("Received request")

#         # Validate required fields
#         for f in ["email", "secret", "task", "nonce", "evaluation_url"]:
#             if f not in data:
#                 return {"status": "error", "message": f"Missing field: {f}"}

#         if data["secret"] != SECRET_KEY:
#             return {"status": "error", "message": "Invalid secret"}

#         brief = data.get("brief", "")
#         task = data["task"]
#         round_num = data.get("round", 1)

#         # Generate files
#         files = generate_files(brief)

#         # Create repo
#         repo_name = f"{task.lower().replace(' ', '-')}-{uuid.uuid4().hex[:6]}"
#         desc = f"Auto-generated for task: {task}"
#         repo = create_repo(repo_name, desc)
#         owner = repo["owner"]["login"]
#         repo_url = repo["html_url"]

#         # Upload files
#         for path, content in files.items():
#             upload_file(owner, repo_name, path, content, f"Add {path}")

#         # README and LICENSE
#         readme = f"# {task}\n\nGenerated automatically.\n\nBrief: {brief}\n"
# #         license_text = f"""MIT License

# # Copyright (c) {time.localtime().tm_year} {AUTHOR}

# # Permission is hereby granted, free of charge, to any person obtaining a copy
# # of this software ... (full MIT text truncated for brevity)
# # """
#         license_text = f"""MIT License

# Copyright (c) {time.localtime().tm_year} {AUTHOR}

# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
# """
        
#         upload_file(owner, repo_name, "README.md", readme, "Add README")
#         upload_file(owner, repo_name, "LICENSE", license_text, "Add LICENSE")

#         # Enable pages
#         enable_pages(owner, repo_name)
#         pages_url = f"https://{owner}.github.io/{repo_name}/"
#         sha = latest_commit(owner, repo_name)

#         # Notify evaluation_url
#         payload = {
#             "email": data["email"],
#             "task": task,
#             "round": round_num,
#             "nonce": data["nonce"],
#             "repo_url": repo_url,
#             "commit_sha": sha,
#             "pages_url": pages_url
#         }
#         try:
#             requests.post(data["evaluation_url"], json=payload, timeout=10)
#         except Exception as e:
#             log(f"Notify failed: {e}")

#         return {"status": "success", "repo_url": repo_url, "pages_url": pages_url, "commit_sha": sha}

#     except Exception as e:
#         log(traceback.format_exc())
#         return {"status": "error", "message": str(e)}


# # ==========================================================
# # Gradio Interface
# # ==========================================================
# iface = gr.Interface(
#     fn=deploy,
#     inputs=gr.Textbox(lines=20, label="Paste JSON request here"),
#     outputs="json",
#     title="LLM App Deployer API",
#     description="Receives JSON request and creates GitHub repo + GitHub Pages."
# )

# if __name__ == "__main__":
#     iface.launch(server_name="0.0.0.0", server_port=int(os.environ.get("PORT", 7860)))

# app.py
# Hugging Face Space: LLM App Deployer API using Gradio
# ------------------------------------------------------
# This Space receives a JSON request, validates a shared secret, calls AIPipe LLM API
# to generate HTML/JS/CSS files, creates a public GitHub repository, uploads files
# (including attachments), enables GitHub Pages, and notifies an evaluation URL.

# import os
# import json
# import base64
# import time
# import uuid
# import traceback
# import requests
# import gradio as gr

# # ===============================
# # CONFIGURATION (from HF Secrets)
# # ===============================
# GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")     # GitHub Personal Access Token
# SECRET_KEY   = os.getenv("SECRET_KEY")       # Secret shared with evaluation system
# APIPIPE_KEY  = os.getenv("APIPIPE_API_KEY")  # from AIPipe.org
# AUTHOR       = os.getenv("AUTHOR", "student")
# GITHUB_API   = "https://api.github.com"

# # ===============================
# # Utility Functions
# # ===============================
# def log(msg: str):
#     print("[LOG]", msg, flush=True)


# def gh_headers():
#     if not GITHUB_TOKEN:
#         raise RuntimeError("Missing GITHUB_TOKEN in Space secrets.")
#     return {
#         "Authorization": f"token {GITHUB_TOKEN}",
#         "Accept": "application/vnd.github.v3+json"
#     }


# def create_repo(name: str, desc: str):
#     """Create new public GitHub repository"""
#     payload = {"name": name, "description": desc, "auto_init": True, "private": False}
#     r = requests.post(f"{GITHUB_API}/user/repos", headers=gh_headers(), json=payload)
#     if r.status_code >= 300:
#         raise RuntimeError(f"GitHub repo create failed: {r.status_code} {r.text}")
#     return r.json()


# def upload_file(owner: str, repo: str, path: str, content: str, message: str):
#     """Create or update a file in the GitHub repo (safe version with sha detection)."""
#     url = f"{GITHUB_API}/repos/{owner}/{repo}/contents/{path}"
#     b64 = base64.b64encode(content.encode()).decode()

#     # Check if file already exists to get SHA
#     r = requests.get(url, headers=gh_headers())
#     if r.status_code == 200:
#         sha = r.json()["sha"]
#         payload = {"message": message, "content": b64, "sha": sha}
#     else:
#         payload = {"message": message, "content": b64}

#     r = requests.put(url, headers=gh_headers(), json=payload)
#     if r.status_code >= 300:
#         raise RuntimeError(f"Upload {path} failed: {r.status_code} {r.text}")


# def enable_pages(owner: str, repo: str):
#     """Enable GitHub Pages for the repo."""
#     url = f"{GITHUB_API}/repos/{owner}/{repo}/pages"
#     payload = {"source": {"branch": "main", "path": "/"}}
#     r = requests.post(url, headers=gh_headers(), json=payload)
#     if r.status_code >= 300:
#         requests.put(url, headers=gh_headers(), json=payload)  # fallback


# def latest_commit(owner: str, repo: str):
#     """Get the latest commit SHA."""
#     r = requests.get(f"{GITHUB_API}/repos/{owner}/{repo}/commits", headers=gh_headers())
#     if r.status_code >= 300:
#         return "unknown"
#     return r.json()[0]["sha"]

# # ==========================================================
# # AIPipe Code Generator
# # ==========================================================
# def generate_files_via_aipipe(brief: str):
#     """Use AIPipe API to generate app files (index.html, script.js, style.css)."""
#     if not APIPIPE_KEY:
#         raise RuntimeError("Missing APIPIPE_API_KEY secret in Hugging Face Space.")

#     headers = {
#         "Authorization": f"Bearer {APIPIPE_KEY}",
#         "Content-Type": "application/json"
#     }

#     prompt = f"""
# You are an expert web developer. 
# Create a small, self-contained web app (HTML, JS, CSS) that fulfills this brief:
# {brief}

# Respond in JSON with keys:
# - index_html
# - script_js
# - style_css
# """

#     payload = {
#         "model": "gpt-4o-mini",
#         "messages": [
#             {"role": "system", "content": "You write production-ready HTML, CSS, and JS code."},
#             {"role": "user", "content": prompt}
#         ],
#         "max_tokens": 1200,
#         "temperature": 0.7
#     }

#     r = requests.post("https://api.aipipe.org/v1/chat/completions", headers=headers, json=payload, timeout=90)
#     if r.status_code != 200:
#         raise RuntimeError(f"AIPipe API call failed: {r.status_code} {r.text}")

#     data = r.json()
#     content = data["choices"][0]["message"]["content"]

#     try:
#         result = json.loads(content)
#     except Exception:
#         # fallback if model returns text instead of JSON
#         result = {"index_html": content, "script_js": "", "style_css": ""}

#     html = result.get("index_html", "<!doctype html><body>empty</body></html>")
#     js   = result.get("script_js", "")
#     css  = result.get("style_css", "")

#     return {"index.html": html, "script.js": js, "style.css": css}

# # ==========================================================
# # Main Handler
# # ==========================================================
# def deploy(json_input: str):
#     try:
#         data = json.loads(json_input)
#         log("Received request")

#         required = ["email", "secret", "task", "nonce", "evaluation_url"]
#         for f in required:
#             if f not in data:
#                 return {"status": "error", "message": f"Missing field: {f}"}

#         if data["secret"] != SECRET_KEY:
#             return {"status": "error", "message": "Invalid secret key."}

#         brief = data.get("brief", "")
#         task  = data["task"]
#         round_num = data.get("round", 1)
#         attachments = data.get("attachments", [])

#         # 1. Generate files using AIPipe
#         files = generate_files_via_aipipe(brief)

#         # 2. Decode and include attachments
#         for att in attachments:
#             try:
#                 name = att.get("name", "file.txt")
#                 uri  = att.get("url", "")
#                 if uri.startswith("data:"):
#                     # Extract base64 part
#                     b64data = uri.split(",")[1]
#                     content = base64.b64decode(b64data).decode(errors="ignore")
#                     files[name] = content
#             except Exception as e:
#                 log(f"Attachment decode failed: {e}")

#         # 3. Create new GitHub repo
#         repo_name = f"{task.lower().replace(' ', '-')}-{uuid.uuid4().hex[:6]}"
#         desc = f"Auto-generated repo for task: {task}"
#         repo = create_repo(repo_name, desc)
#         owner = repo["owner"]["login"]
#         repo_url = repo["html_url"]

#         # 4. Upload generated files
#         for path, content in files.items():
#             upload_file(owner, repo_name, path, content, f"Add {path}")

#         # 5. Add README and LICENSE
#         readme = f"# {task}\n\nGenerated automatically.\n\nBrief:\n{brief}\n"
#         license_text = f"""MIT License

# Copyright (c) {time.localtime().tm_year} {AUTHOR}

# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
# """

#         upload_file(owner, repo_name, "README.md", readme, "Add README")
#         upload_file(owner, repo_name, "LICENSE", license_text, "Add LICENSE")

#         # 6. Enable GitHub Pages
#         enable_pages(owner, repo_name)
#         pages_url = f"https://{owner}.github.io/{repo_name}/"
#         sha = latest_commit(owner, repo_name)

#         # 7. Notify evaluation URL
#         payload = {
#             "email": data["email"],
#             "task": task,
#             "round": round_num,
#             "nonce": data["nonce"],
#             "repo_url": repo_url,
#             "commit_sha": sha,
#             "pages_url": pages_url
#         }

#         try:
#             requests.post(data["evaluation_url"], json=payload, timeout=10)
#         except Exception as e:
#             log(f"Notify evaluation URL failed: {e}")

#         # Final API response
#         return {
#             "status": "success",
#             "repo_url": repo_url,
#             "pages_url": pages_url,
#             "commit_sha": sha
#         }

#     except Exception as e:
#         log(traceback.format_exc())
#         return {"status": "error", "message": str(e)}

# # ==========================================================
# # Gradio Interface
# # ==========================================================
# iface = gr.Interface(
#     fn=deploy,
#     inputs=gr.Textbox(lines=20, label="Paste JSON request here"),
#     outputs="json",
#     title="LLM App Deployer API (via AIPipe)",
#     description=(
#         "Receives a JSON request, calls AIPipe to generate HTML/JS/CSS, "
#         "creates a GitHub repo with GitHub Pages, and notifies evaluation URL."
#     ),
# )

# if __name__ == "__main__":
#     iface.launch(server_name="0.0.0.0", server_port=int(os.environ.get("PORT", 7860)))

# import os
# import json
# import base64
# import time
# import uuid
# import traceback
# import requests
# import gradio as gr
# from openai import OpenAI

# GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
# SECRET_KEY = os.getenv("SECRET_KEY")
# APIPIPE_KEY = os.getenv("APIPIPE_API_KEY")
# AUTHOR = os.getenv("AUTHOR", "student")
# GITHUB_API = "https://api.github.com"

# def log(msg):
#     print("[LOG]", msg, flush=True)

# def gh_headers():
#     if not GITHUB_TOKEN:
#         raise RuntimeError("Missing GITHUB_TOKEN in Space secrets.")
#     return {"Authorization": f"token {GITHUB_TOKEN}", "Accept": "application/vnd.github.v3+json"}

# def create_repo(name, desc):
#     payload = {"name": name, "description": desc, "auto_init": True, "private": False}
#     r = requests.post(f"{GITHUB_API}/user/repos", headers=gh_headers(), json=payload)
#     if r.status_code >= 300:
#         raise RuntimeError(f"GitHub repo create failed: {r.status_code} {r.text}")
#     return r.json()

# def upload_file(owner, repo, path, content, message):
#     url = f"{GITHUB_API}/repos/{owner}/{repo}/contents/{path}"
#     b64 = base64.b64encode(content.encode()).decode()
#     r = requests.get(url, headers=gh_headers())
#     if r.status_code == 200:
#         sha = r.json()["sha"]
#         payload = {"message": message, "content": b64, "sha": sha}
#     else:
#         payload = {"message": message, "content": b64}
#     r = requests.put(url, headers=gh_headers(), json=payload)
#     if r.status_code >= 300:
#         raise RuntimeError(f"Upload {path} failed: {r.status_code} {r.text}")

# def enable_pages(owner, repo):
#     url = f"{GITHUB_API}/repos/{owner}/{repo}/pages"
#     payload = {"source": {"branch": "main", "path": "/"}}
#     r = requests.post(url, headers=gh_headers(), json=payload)
#     if r.status_code >= 300:
#         requests.put(url, headers=gh_headers(), json=payload)

# def latest_commit(owner, repo):
#     r = requests.get(f"{GITHUB_API}/repos/{owner}/{repo}/commits", headers=gh_headers())
#     if r.status_code >= 300:
#         return "unknown"
#     return r.json()[0]["sha"]

# def generate_files_via_aipipe(brief):
#     if not APIPIPE_KEY:
#         raise RuntimeError("Missing APIPIPE_API_KEY secret.")
#     client = OpenAI(api_key=APIPIPE_KEY, base_url="https://api.aipipe.org/v1")
#     prompt = f"You are an expert web developer. Create a small, self-contained web app (HTML, JS, CSS) that fulfills this brief: {brief}. Respond in JSON with keys index_html, script_js, style_css."
#     completion = client.chat.completions.create(
#         model="gpt-4o-mini",
#         messages=[
#             {"role": "system", "content": "You write production-ready HTML, CSS, and JS code."},
#             {"role": "user", "content": prompt}
#         ],
#         max_tokens=1200,
#         temperature=0.7
#     )
#     content = completion.choices[0].message.content
#     try:
#         result = json.loads(content)
#     except Exception:
#         result = {"index_html": content, "script_js": "", "style_css": ""}
#     html = result.get("index_html", "<!doctype html><body>empty</body></html>")
#     js = result.get("script_js", "")
#     css = result.get("style_css", "")
#     return {"index.html": html, "script.js": js, "style.css": css}

# def deploy(json_input):
#     try:
#         data = json.loads(json_input)
#         log("Received request")
#         for f in ["email", "secret", "task", "nonce", "evaluation_url"]:
#             if f not in data:
#                 return {"status": "error", "message": f"Missing field: {f}"}
#         if data["secret"] != SECRET_KEY:
#             return {"status": "error", "message": "Invalid secret key."}
#         brief = data.get("brief", "")
#         task = data["task"]
#         round_num = data.get("round", 1)
#         attachments = data.get("attachments", [])
#         files = generate_files_via_aipipe(brief)
#         for att in attachments:
#             try:
#                 name = att.get("name", "file.txt")
#                 uri = att.get("url", "")
#                 if uri.startswith("data:"):
#                     b64data = uri.split(",")[1]
#                     content = base64.b64decode(b64data).decode(errors="ignore")
#                     files[name] = content
#             except Exception as e:
#                 log(f"Attachment decode failed: {e}")
#         repo_name = f"{task.lower().replace(' ', '-')}-{uuid.uuid4().hex[:6]}"
#         desc = f"Auto-generated repo for task: {task}"
#         repo = create_repo(repo_name, desc)
#         owner = repo["owner"]["login"]
#         repo_url = repo["html_url"]
#         for path, content in files.items():
#             upload_file(owner, repo_name, path, content, f"Add {path}")
#         readme = f"# {task}\n\nGenerated automatically.\n\nBrief:\n{brief}\n"
#         license_text = f"""MIT License
# Copyright (c) {time.localtime().tm_year} {AUTHOR}
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
# """
#         upload_file(owner, repo_name, "README.md", readme, "Add README")
#         upload_file(owner, repo_name, "LICENSE", license_text, "Add LICENSE")
#         enable_pages(owner, repo_name)
#         pages_url = f"https://{owner}.github.io/{repo_name}/"
#         sha = latest_commit(owner, repo_name)
#         payload = {"email": data["email"], "task": task, "round": round_num, "nonce": data["nonce"], "repo_url": repo_url, "commit_sha": sha, "pages_url": pages_url}
#         try:
#             requests.post(data["evaluation_url"], json=payload, timeout=10)
#         except Exception as e:
#             log(f"Notify evaluation URL failed: {e}")
#         return {"status": "success", "repo_url": repo_url, "pages_url": pages_url, "commit_sha": sha}
#     except Exception as e:
#         log(traceback.format_exc())
#         return {"status": "error", "message": str(e)}

# iface = gr.Interface(
#     fn=deploy,
#     inputs=gr.Textbox(lines=20, label="Paste JSON request here"),
#     outputs="json",
#     title="LLM App Deployer API (via AIPipe)",
#     description="Receives JSON, uses AIPipe-compatible OpenAI client to generate HTML/JS/CSS, creates a GitHub repo with Pages, and notifies evaluation URL."
# )

# if __name__ == "__main__":
#     iface.launch(server_name="0.0.0.0", server_port=int(os.environ.get("PORT", 7860)))


# import os
# import json
# import base64
# import time
# import uuid
# import traceback
# import requests
# import gradio as gr
# from openai import OpenAI

# # --- Environment Variables ---
# GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
# SECRET_KEY = os.getenv("SECRET_KEY")
# APIPIPE_KEY = os.getenv("APIPIPE_API_KEY")
# AUTHOR = os.getenv("AUTHOR", "student")
# GITHUB_API = "https://api.github.com"


# def log(msg):
#     """Prints a log message to the console."""
#     print("[LOG]", msg, flush=True)


# def gh_headers():
#     """Returns headers for GitHub API requests."""
#     if not GITHUB_TOKEN:
#         raise RuntimeError("Missing GITHUB_TOKEN in Space secrets.")
#     return {
#         "Authorization": f"token {GITHUB_TOKEN}",
#         "Accept": "application/vnd.github.v3+json",
#     }


# def create_repo(name, desc):
#     """Creates a new public GitHub repository."""
#     payload = {"name": name, "description": desc, "auto_init": True, "private": False}
#     r = requests.post(f"{GITHUB_API}/user/repos", headers=gh_headers(), json=payload)
#     if r.status_code >= 300:
#         raise RuntimeError(f"GitHub repo create failed: {r.status_code} {r.text}")
#     return r.json()


# def upload_file(owner, repo, path, content, message):
#     """Uploads or updates a file in a GitHub repository."""
#     url = f"{GITHUB_API}/repos/{owner}/{repo}/contents/{path}"
#     b64 = base64.b64encode(content.encode('utf-8')).decode('utf-8')
    
#     # Check if the file already exists to get its SHA
#     r = requests.get(url, headers=gh_headers())
#     sha = None
#     if r.status_code == 200:
#         sha = r.json().get("sha")

#     payload = {"message": message, "content": b64}
#     if sha:
#         payload["sha"] = sha
        
#     r = requests.put(url, headers=gh_headers(), json=payload)
#     if r.status_code >= 300:
#         raise RuntimeError(f"Upload {path} failed: {r.status_code} {r.text}")


# def enable_pages(owner, repo):
#     """Enables GitHub Pages for a repository."""
#     url = f"{GITHUB_API}/repos/{owner}/{repo}/pages"
#     payload = {"source": {"branch": "main", "path": "/"}}
#     headers = gh_headers()
#     headers["Accept"] = "application/vnd.github.switcheroo-preview+json" # Required header for pages API
#     r = requests.post(url, headers=headers, json=payload)
#     # A 201 status code is a success for creation. If it already exists, we might get another code.
#     if r.status_code >= 300:
#         # If posting fails, try updating
#         requests.put(url, headers=headers, json=payload)


# def latest_commit(owner, repo):
#     """Gets the SHA of the latest commit on the main branch."""
#     r = requests.get(f"{GITHUB_API}/repos/{owner}/{repo}/commits/main", headers=gh_headers())
#     if r.status_code >= 300:
#         return "unknown"
#     return r.json()["sha"]


# def generate_files_via_aipipe(brief):
#     """Generates web app files using the AIPipe API."""
#     if not APIPIPE_KEY:
#         raise RuntimeError("Missing APIPIPE_API_KEY secret.")

#     # FIX: Corrected base_url from 'https://api.aipipe.org/v1' to 'https://aipipe.org/openrouter/v1'
#     # FIX: Updated model to match the one in the usage example.
#     client = OpenAI(api_key=APIPIPE_KEY, base_url="https://aipipe.org/openrouter/v1")
    
#     prompt = f"You are an expert web developer. Create a small, self-contained web app (HTML, JS, CSS) that fulfills this brief: {brief}. Respond ONLY in valid JSON format with three keys: `index_html`, `script_js`, `style_css`. Do not add any text before or after the JSON object."
    
#     completion = client.chat.completions.create(
#         model="openai/gpt-4.1-nano",
#         messages=[
#             {"role": "system", "content": "You write production-ready HTML, CSS, and JS code and respond in pure JSON."},
#             {"role": "user", "content": prompt}
#         ],
#         max_tokens=2048,
#         temperature=0.7,
#         response_format={"type": "json_object"} # Use JSON mode for reliable output
#     )
#     content = completion.choices[0].message.content
    
#     try:
#         # The content should be a valid JSON string
#         result = json.loads(content)
#     except json.JSONDecodeError:
#         log(f"Failed to parse LLM response as JSON. Content: {content}")
#         # Fallback for non-JSON responses
#         result = {"index_html": content, "script_js": "", "style_css": ""}

#     html = result.get("index_html", "<!doctype html><html><body><h1>Error</h1><p>Failed to generate content.</p></body></html>")
#     js = result.get("script_js", "")
#     css = result.get("style_css", "")
    
#     # Combine into a single HTML file for simplicity with GitHub Pages
#     full_html = f"""<!DOCTYPE html>
# <html lang="en">
# <head>
#     <meta charset="UTF-8">
#     <meta name="viewport" content="width=device-width, initial-scale=1.0">
#     <title>Generated App</title>
#     <style>
# {css}
#     </style>
# </head>
# <body>
# {html}
#     <script>
# {js}
#     </script>
# </body>
# </html>"""

#     return {"index.html": full_html}


# def deploy(json_input):
#     """Main function to handle the deployment request."""
#     try:
#         data = json.loads(json_input)
#         log("Received request")
        
#         required_fields = ["email", "secret", "task", "nonce", "evaluation_url"]
#         for f in required_fields:
#             if f not in data:
#                 return {"status": "error", "message": f"Missing field: {f}"}
                
#         if data["secret"] != SECRET_KEY:
#             return {"status": "error", "message": "Invalid secret key."}
            
#         brief = data.get("brief", "Create a simple hello world page.")
#         task = data["task"]
#         round_num = data.get("round", 1)
#         attachments = data.get("attachments", [])
        
#         # Augment the brief with information from attachments for the LLM
#         if attachments:
#             brief += "\n\nThe user has provided the following attachments which should be used in the app:"
#             for att in attachments:
#                 name = att.get("name", "file")
#                 brief += f"\n- {name}"

#         files = generate_files_via_aipipe(brief)
        
#         # Handle attachments by including them in the project files
#         for att in attachments:
#             try:
#                 name = att.get("name", "file.txt")
#                 uri = att.get("url", "")
#                 if uri.startswith("data:"):
#                     # format: data:<mime_type>;base64,<data>
#                     header, b64data = uri.split(",", 1)
#                     content = base64.b64decode(b64data).decode(errors="ignore")
#                     files[name] = content
#             except Exception as e:
#                 log(f"Attachment decode failed for '{name}': {e}")
                
#         repo_name = f"{task.lower().replace(' ', '-')}-{uuid.uuid4().hex[:6]}"
#         desc = f"Auto-generated repo for task: {task}"
        
#         repo = create_repo(repo_name, desc)
#         owner = repo["owner"]["login"]
#         repo_url = repo["html_url"]
        
#         for path, content in files.items():
#             upload_file(owner, repo_name, path, content, f"Add {path}")
            
#         readme = f"# {task}\n\nGenerated automatically for the TDS project.\n\n## Brief\n\n{brief}\n"
#         license_text = f"""MIT License

# Copyright (c) {time.localtime().tm_year} {AUTHOR}

# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE."""

#         upload_file(owner, repo_name, "README.md", readme, "Add README")
#         upload_file(owner, repo_name, "LICENSE", license_text, "Add LICENSE")
        
#         enable_pages(owner, repo_name)
#         pages_url = f"https://{owner}.github.io/{repo_name}/"
        
#         # Wait a moment for commit to be available
#         time.sleep(5) 
#         sha = latest_commit(owner, repo_name)
        
#         payload = {
#             "email": data["email"], 
#             "task": task, 
#             "round": round_num, 
#             "nonce": data["nonce"], 
#             "repo_url": repo_url, 
#             "commit_sha": sha, 
#             "pages_url": pages_url
#         }
        
#         try:
#             # Notify the evaluation URL about the deployment
#             requests.post(data["evaluation_url"], json=payload, timeout=10)
#         except requests.exceptions.RequestException as e:
#             log(f"Notify evaluation URL failed: {e}")
            
#         return {"status": "success", "repo_url": repo_url, "pages_url": pages_url, "commit_sha": sha}

#     except Exception as e:
#         log(traceback.format_exc())
#         return {"status": "error", "message": str(e)}

# # --- Gradio Interface ---
# iface = gr.Interface(
#     fn=deploy,
#     inputs=gr.Textbox(lines=20, label="Paste JSON request here", info="The full JSON payload for the deployment request."),
#     outputs=gr.JSON(label="API Response"),
#     title="LLM App Deployer (via AIPipe)",
#     description="Receives a JSON request, uses an AIPipe-compatible OpenAI client to generate a web app, creates a GitHub repo with Pages, and notifies an evaluation URL.",
#     allow_flagging="never"
# )

# if __name__ == "__main__":
#     iface.launch(server_name="0.0.0.0", server_port=int(os.environ.get("PORT", 7860)))


# import os
# import json
# import base64
# import time
# import uuid
# import traceback
# import requests
# import gradio as gr
# from openai import OpenAI
# import hashlib

# # --- Environment Variables ---
# GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
# SECRET_KEY = os.getenv("SECRET_KEY")
# APIPIPE_KEY = os.getenv("APIPIPE_API_KEY")
# AUTHOR = os.getenv("AUTHOR", "student")
# GITHUB_API = "https://api.github.com"


# def log(msg):
#     """Prints a log message to the console."""
#     print("[LOG]", msg, flush=True)


# def gh_headers():
#     """Returns headers for GitHub API requests."""
#     if not GITHUB_TOKEN:
#         raise RuntimeError("Missing GITHUB_TOKEN in Space secrets.")
#     return {
#         "Authorization": f"token {GITHUB_TOKEN}",
#         "Accept": "application/vnd.github.v3+json",
#     }

# def get_github_user():
#     """Gets the authenticated GitHub user's login name."""
#     r = requests.get(f"{GITHUB_API}/user", headers=gh_headers())
#     if r.status_code >= 300:
#         raise RuntimeError(f"Failed to get GitHub user: {r.status_code} {r.text}")
#     return r.json()["login"]

# def get_repo(owner, repo_name):
#     """Gets details of a specific repository, returning None if not found."""
#     url = f"{GITHUB_API}/repos/{owner}/{repo_name}"
#     r = requests.get(url, headers=gh_headers())
#     if r.status_code == 200:
#         return r.json()
#     return None

# def create_repo(name, desc):
#     """Creates a new public GitHub repository."""
#     payload = {"name": name, "description": desc, "auto_init": True, "private": False}
#     r = requests.post(f"{GITHUB_API}/user/repos", headers=gh_headers(), json=payload)
#     if r.status_code >= 300:
#         raise RuntimeError(f"GitHub repo create failed: {r.status_code} {r.text}")
#     return r.json()


# def upload_file(owner, repo, path, content, message):
#     """Uploads or updates a file in a GitHub repository."""
#     url = f"{GITHUB_API}/repos/{owner}/{repo}/contents/{path}"
#     b64 = base64.b64encode(content.encode('utf-8')).decode('utf-8')
    
#     r = requests.get(url, headers=gh_headers())
#     sha = r.json().get("sha") if r.status_code == 200 else None

#     payload = {"message": message, "content": b64}
#     if sha:
#         payload["sha"] = sha
        
#     r = requests.put(url, headers=gh_headers(), json=payload)
#     if r.status_code >= 300:
#         raise RuntimeError(f"Upload {path} failed: {r.status_code} {r.text}")


# def enable_pages(owner, repo):
#     """Enables GitHub Pages for a repository."""
#     url = f"{GITHUB_API}/repos/{owner}/{repo}/pages"
#     payload = {"source": {"branch": "main", "path": "/"}}
#     headers = gh_headers()
#     headers["Accept"] = "application/vnd.github.switcheroo-preview+json"
#     r = requests.post(url, headers=headers, json=payload)
#     if r.status_code >= 300 and r.status_code != 409: # 409 means it might already be enabled
#         requests.put(url, headers=headers, json=payload)


# def latest_commit(owner, repo):
#     """Gets the SHA of the latest commit on the main branch."""
#     r = requests.get(f"{GITHUB_API}/repos/{owner}/{repo}/commits/main", headers=gh_headers())
#     if r.status_code >= 300:
#         return "unknown"
#     return r.json()["sha"]


# def generate_files_via_aipipe(brief):
#     """Generates web app files using the AIPipe API."""
#     if not APIPIPE_KEY:
#         raise RuntimeError("Missing APIPIPE_API_KEY secret.")

#     client = OpenAI(api_key=APIPIPE_KEY, base_url="https://aipipe.org/openrouter/v1")
    
#     prompt = f"You are an expert web developer. Create a small, self-contained web app (HTML, JS, CSS) that fulfills this brief: {brief}. Respond ONLY in valid JSON format with three keys: `index_html`, `script_js`, `style_css`. Do not add any text before or after the JSON object."
    
#     completion = client.chat.completions.create(
#         model="openai/gpt-4.1-nano",
#         messages=[
#             {"role": "system", "content": "You write production-ready HTML, CSS, and JS code and respond in pure JSON."},
#             {"role": "user", "content": prompt}
#         ],
#         max_tokens=2048,
#         temperature=0.7,
#         response_format={"type": "json_object"}
#     )
#     content = completion.choices[0].message.content
    
#     try:
#         result = json.loads(content)
#     except json.JSONDecodeError:
#         log(f"Failed to parse LLM response as JSON. Content: {content}")
#         result = {"index_html": content, "script_js": "", "style_css": ""}

#     html_content = result.get("index_html", "<h1>Error</h1><p>Failed to generate content.</p>")
#     js_content = result.get("script_js", "")
#     css_content = result.get("style_css", "")
    
#     full_html = f"""<!DOCTYPE html>
# <html lang="en">
# <head>
#     <meta charset="UTF-8">
#     <meta name="viewport" content="width=device-width, initial-scale=1.0">
#     <title>Generated App</title>
#     <style>{css_content}</style>
# </head>
# <body>
# {html_content}
#     <script>{js_content}</script>
# </body>
# </html>"""

#     return {"index.html": full_html}


# def deploy(json_input):
#     """Main function to handle the deployment request."""
#     try:
#         data = json.loads(json_input)
#         log("Received request")
        
#         required_fields = ["email", "secret", "task", "nonce", "evaluation_url"]
#         for f in required_fields:
#             if f not in data:
#                 return json.dumps({"status": "error", "message": f"Missing field: {f}"})
                
#         if data["secret"] != SECRET_KEY:
#             return json.dumps({"status": "error", "message": "Invalid secret key."})
            
#         brief = data.get("brief", "Create a simple hello world page.")
#         task = data["task"]
#         round_num = data.get("round", 1)
#         attachments = data.get("attachments", [])
        
#         # --- Deterministic Repo Naming for Updates ---
#         task_slug = task.lower().replace(' ', '-')
#         stable_id = hashlib.sha256(f"{data['email']}{task}".encode()).hexdigest()[:8]
#         repo_name = f"{task_slug}-{stable_id}"
        
#         owner = get_github_user()
#         repo = get_repo(owner, repo_name)

#         if repo is None:
#             if round_num > 1:
#                 return json.dumps({"status": "error", "message": f"Repo '{repo_name}' not found for a round 2 update."})
#             log(f"Repo '{repo_name}' not found. Creating it.")
#             desc = f"Auto-generated repo for task: {task}"
#             repo = create_repo(repo_name, desc)
#             enable_pages(owner, repo_name)
#         else:
#             log(f"Found existing repo '{repo_name}'. Updating it.")

#         repo_url = repo["html_url"]

#         if attachments:
#             brief += "\n\nThis app should use the following attachments:"
#             for att in attachments:
#                 brief += f"\n- {att.get('name', 'file')}"

#         files = generate_files_via_aipipe(brief)
        
#         for att in attachments:
#             try:
#                 name = att.get("name", "file.txt")
#                 uri = att.get("url", "")
#                 if uri.startswith("data:"):
#                     header, b64data = uri.split(",", 1)
#                     content = base64.b64decode(b64data).decode(errors="ignore")
#                     files[name] = content
#             except Exception as e:
#                 log(f"Attachment decode failed for '{name}': {e}")
                
#         for path, content in files.items():
#             upload_file(owner, repo_name, path, content, f"Update {path} for round {round_num}")
            
#         readme = f"# {task}\n\nRound: {round_num}\n\nBrief:\n{brief}\n"
#         license_text = f"MIT License\n\nCopyright (c) {time.localtime().tm_year} {AUTHOR}\n\n..."

#         upload_file(owner, repo_name, "README.md", readme, "Update README")
#         upload_file(owner, repo_name, "LICENSE", license_text, "Update LICENSE")
        
#         pages_url = f"https://{owner}.github.io/{repo_name}/"
        
#         time.sleep(5) 
#         sha = latest_commit(owner, repo_name)
        
#         payload = {
#             "email": data["email"], "task": task, "round": round_num, "nonce": data["nonce"], 
#             "repo_url": repo_url, "commit_sha": sha, "pages_url": pages_url
#         }
        
#         try:
#             requests.post(data["evaluation_url"], json=payload, timeout=10)
#         except requests.exceptions.RequestException as e:
#             log(f"Notify evaluation URL failed: {e}")
            
#         return json.dumps({"status": "success", "repo_url": repo_url, "pages_url": pages_url, "commit_sha": sha})

#     except Exception as e:
#         log(traceback.format_exc())
#         return json.dumps({"status": "error", "message": str(e)})

# # --- Gradio Interface ---
# iface = gr.Interface(
#     fn=deploy,
#     inputs=gr.Textbox(lines=20, label="Paste JSON request here"),
#     outputs="json",
#     title="LLM App Deployer API (via AIPipe)",
#     description="Receives JSON, uses AIPipe-compatible OpenAI client to generate HTML/JS/CSS, creates/updates a GitHub repo, and notifies evaluation URL.",
#     # FIX: Explicitly name the API endpoint to fix 404/405 errors.
#     api_name="predict",
#     # FIX: Use the updated parameter to disable flagging and avoid warnings.
#     flagging_options=None 
# )

# if __name__ == "__main__":
#     iface.launch(server_name="0.0.0.0", server_port=int(os.environ.get("PORT", 7860)))


# import os
# import json
# import base64
# import time
# import uuid
# import traceback
# import requests
# import gradio as gr
# from openai import OpenAI
# import hashlib
# import threading

# # --- Environment Variables ---
# GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
# SECRET_KEY = os.getenv("SECRET_KEY")
# APIPIPE_KEY = os.getenv("APIPIPE_API_KEY")
# AUTHOR = os.getenv("AUTHOR", "student")
# GITHUB_API = "https://api.github.com"


# def log(msg):
#     """Prints a log message to the console."""
#     print("[LOG]", msg, flush=True)


# def gh_headers():
#     """Returns headers for GitHub API requests."""
#     if not GITHUB_TOKEN:
#         raise RuntimeError("Missing GITHUB_TOKEN in Space secrets.")
#     return {
#         "Authorization": f"token {GITHUB_TOKEN}",
#         "Accept": "application/vnd.github.v3+json",
#     }

# def get_github_user():
#     """Gets the authenticated GitHub user's login name."""
#     r = requests.get(f"{GITHUB_API}/user", headers=gh_headers())
#     if r.status_code >= 300:
#         raise RuntimeError(f"Failed to get GitHub user: {r.status_code} {r.text}")
#     return r.json()["login"]

# def get_repo(owner, repo_name):
#     """Gets details of a specific repository, returning None if not found."""
#     url = f"{GITHUB_API}/repos/{owner}/{repo_name}"
#     r = requests.get(url, headers=gh_headers())
#     if r.status_code == 200:
#         return r.json()
#     return None

# def create_repo(name, desc):
#     """Creates a new public GitHub repository."""
#     payload = {"name": name, "description": desc, "auto_init": True, "private": False}
#     r = requests.post(f"{GITHUB_API}/user/repos", headers=gh_headers(), json=payload)
#     if r.status_code >= 300:
#         raise RuntimeError(f"GitHub repo create failed: {r.status_code} {r.text}")
#     return r.json()


# def upload_file(owner, repo, path, content, message):
#     """Uploads or updates a file in a GitHub repository."""
#     url = f"{GITHUB_API}/repos/{owner}/{repo}/contents/{path}"
#     b64 = base64.b64encode(content.encode('utf-8')).decode('utf-8')
    
#     r = requests.get(url, headers=gh_headers())
#     sha = r.json().get("sha") if r.status_code == 200 else None

#     payload = {"message": message, "content": b64}
#     if sha:
#         payload["sha"] = sha
        
#     r = requests.put(url, headers=gh_headers(), json=payload)
#     if r.status_code >= 300:
#         raise RuntimeError(f"Upload {path} failed: {r.status_code} {r.text}")


# def enable_pages(owner, repo):
#     """Enables GitHub Pages for a repository."""
#     url = f"{GITHUB_API}/repos/{owner}/{repo}/pages"
#     payload = {"source": {"branch": "main", "path": "/"}}
#     headers = gh_headers()
#     headers["Accept"] = "application/vnd.github.switcheroo-preview+json"
#     r = requests.post(url, headers=headers, json=payload)
#     if r.status_code >= 300 and r.status_code != 409: # 409 means it might already be enabled
#         requests.put(url, headers=headers, json=payload)


# def latest_commit(owner, repo):
#     """Gets the SHA of the latest commit on the main branch."""
#     r = requests.get(f"{GITHUB_API}/repos/{owner}/{repo}/commits/main", headers=gh_headers())
#     if r.status_code >= 300:
#         return "unknown"
#     return r.json()["sha"]


# def generate_files_via_aipipe(brief):
#     """Generates web app files using the AIPipe API."""
#     if not APIPIPE_KEY:
#         raise RuntimeError("Missing APIPIPE_API_KEY secret.")

#     client = OpenAI(api_key=APIPIPE_KEY, base_url="https://aipipe.org/openrouter/v1")
    
#     prompt = f"You are an expert web developer. Create a small, self-contained web app (HTML, JS, CSS) that fulfills this brief: {brief}. Respond ONLY in valid JSON format with three keys: `index_html`, `script_js`, `style_css`. Do not add any text before or after the JSON object."
    
#     completion = client.chat.completions.create(
#         model="openai/gpt-4.1-nano",
#         messages=[
#             {"role": "system", "content": "You write production-ready HTML, CSS, and JS code and respond in pure JSON."},
#             {"role": "user", "content": prompt}
#         ],
#         max_tokens=2048,
#         temperature=0.7,
#         response_format={"type": "json_object"}
#     )
#     content = completion.choices[0].message.content
    
#     try:
#         result = json.loads(content)
#     except json.JSONDecodeError:
#         log(f"Failed to parse LLM response as JSON. Content: {content}")
#         result = {"index_html": content, "script_js": "", "style_css": ""}

#     html_content = result.get("index_html", "<h1>Error</h1><p>Failed to generate content.</p>")
#     js_content = result.get("script_js", "")
#     css_content = result.get("style_css", "")
    
#     full_html = f"""<!DOCTYPE html>
# <html lang="en">
# <head>
#     <meta charset="UTF-8">
#     <meta name="viewport" content="width=device-width, initial-scale=1.0">
#     <title>Generated App</title>
#     <style>{css_content}</style>
# </head>
# <body>
# {html_content}
#     <script>{js_content}</script>
# </body>
# </html>"""

#     return {"index.html": full_html}


# def deploy(json_input):
#     """Main function to handle the deployment request."""
#     try:
#         data = json.loads(json_input)
#         log("Received request")
        
#         required_fields = ["email", "secret", "task", "nonce", "evaluation_url"]
#         for f in required_fields:
#             if f not in data:
#                 return json.dumps({"status": "error", "message": f"Missing field: {f}"})
                
#         if data["secret"] != SECRET_KEY:
#             return json.dumps({"status": "error", "message": "Invalid secret key."})
            
#         brief = data.get("brief", "Create a simple hello world page.")
#         task = data["task"]
#         round_num = data.get("round", 1)
#         attachments = data.get("attachments", [])
        
#         # --- Deterministic Repo Naming for Updates ---
#         task_slug = task.lower().replace(' ', '-')
#         stable_id = hashlib.sha256(f"{data['email']}{task}".encode()).hexdigest()[:8]
#         repo_name = f"{task_slug}-{stable_id}"
        
#         owner = get_github_user()
#         repo = get_repo(owner, repo_name)

#         if repo is None:
#             if round_num > 1:
#                 return json.dumps({"status": "error", "message": f"Repo '{repo_name}' not found for a round 2 update."})
#             log(f"Repo '{repo_name}' not found. Creating it.")
#             desc = f"Auto-generated repo for task: {task}"
#             repo = create_repo(repo_name, desc)
#             enable_pages(owner, repo_name)
#         else:
#             log(f"Found existing repo '{repo_name}'. Updating it.")

#         repo_url = repo["html_url"]

#         if attachments:
#             brief += "\n\nThis app should use the following attachments:"
#             for att in attachments:
#                 brief += f"\n- {att.get('name', 'file')}"

#         files = generate_files_via_aipipe(brief)
        
#         for att in attachments:
#             try:
#                 name = att.get("name", "file.txt")
#                 uri = att.get("url", "")
#                 if uri.startswith("data:"):
#                     header, b64data = uri.split(",", 1)
#                     content = base64.b64decode(b64data).decode(errors="ignore")
#                     files[name] = content
#             except Exception as e:
#                 log(f"Attachment decode failed for '{name}': {e}")
                
#         for path, content in files.items():
#             upload_file(owner, repo_name, path, content, f"Update {path} for round {round_num}")
            
#         readme = f"# {task}\n\nRound: {round_num}\n\nBrief:\n{brief}\n"
#         license_text = f"MIT License\n\nCopyright (c) {time.localtime().tm_year} {AUTHOR}\n\n..."

#         upload_file(owner, repo_name, "README.md", readme, "Update README")
#         upload_file(owner, repo_name, "LICENSE", license_text, "Update LICENSE")
        
#         pages_url = f"https://{owner}.github.io/{repo_name}/"
        
#         time.sleep(5) 
#         sha = latest_commit(owner, repo_name)
        
#         payload = {
#             "email": data["email"], "task": task, "round": round_num, "nonce": data["nonce"], 
#             "repo_url": repo_url, "commit_sha": sha, "pages_url": pages_url
#         }
        
#         # --- Non-blocking notification to avoid timeouts ---
#         def notify_evaluation_url(url, json_payload):
#             """Sends a POST request in a separate thread."""
#             try:
#                 # Increased timeout for safety, though it won't block the main response.
#                 requests.post(url, json=json_payload, timeout=20)
#                 log(f"Successfully notified evaluation URL: {url}")
#             except requests.exceptions.RequestException as e:
#                 log(f"Notify evaluation URL failed in background thread: {e}")

#         # Start the notification in a background thread
#         notification_thread = threading.Thread(
#             target=notify_evaluation_url,
#             args=(data["evaluation_url"], payload)
#         )
#         notification_thread.start()
            
#         return json.dumps({"status": "success", "repo_url": repo_url, "pages_url": pages_url, "commit_sha": sha})

#     except Exception as e:
#         log(traceback.format_exc())
#         return json.dumps({"status": "error", "message": str(e)})

# # --- Gradio Interface ---
# iface = gr.Interface(
#     fn=deploy,
#     inputs=gr.Textbox(lines=20, label="Paste JSON request here"),
#     outputs="json",
#     title="LLM App Deployer API (via AIPipe)",
#     description="Receives JSON, uses AIPipe-compatible OpenAI client to generate HTML/JS/CSS, creates/updates a GitHub repo, and notifies evaluation URL.",
#     api_name="predict",
#     flagging_options=None 
# )

# if __name__ == "__main__":
#     iface.launch(server_name="0.0.0.0", server_port=int(os.environ.get("PORT", 7860)))

import os
import json
import base64
import time
import uuid
import traceback
import requests
import gradio as gr
from openai import OpenAI
import hashlib
import threading

# --- Environment Variables ---
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
SECRET_KEY = os.getenv("SECRET_KEY")
APIPIPE_KEY = os.getenv("APIPIPE_API_KEY")
AUTHOR = os.getenv("AUTHOR", "student")
GITHUB_API = "https://api.github.com"


def log(msg):
    """Prints a log message to the console."""
    print("[LOG]", msg, flush=True)


def gh_headers():
    """Returns headers for GitHub API requests."""
    if not GITHUB_TOKEN:
        raise RuntimeError("Missing GITHUB_TOKEN in Space secrets.")
    return {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json",
    }

def get_github_user():
    """Gets the authenticated GitHub user's login name."""
    r = requests.get(f"{GITHUB_API}/user", headers=gh_headers())
    if r.status_code >= 300:
        raise RuntimeError(f"Failed to get GitHub user: {r.status_code} {r.text}")
    return r.json()["login"]

def get_repo(owner, repo_name):
    """Gets details of a specific repository, returning None if not found."""
    url = f"{GITHUB_API}/repos/{owner}/{repo_name}"
    r = requests.get(url, headers=gh_headers())
    if r.status_code == 200:
        return r.json()
    return None

def create_repo(name, desc):
    """Creates a new public GitHub repository."""
    payload = {"name": name, "description": desc, "auto_init": True, "private": False}
    r = requests.post(f"{GITHUB_API}/user/repos", headers=gh_headers(), json=payload)
    if r.status_code >= 300:
        raise RuntimeError(f"GitHub repo create failed: {r.status_code} {r.text}")
    return r.json()


def upload_file(owner, repo, path, content, message):
    """Uploads or updates a file in a GitHub repository."""
    url = f"{GITHUB_API}/repos/{owner}/{repo}/contents/{path}"
    b64 = base64.b64encode(content.encode('utf-8')).decode('utf-8')
    
    r = requests.get(url, headers=gh_headers())
    sha = r.json().get("sha") if r.status_code == 200 else None

    payload = {"message": message, "content": b64}
    if sha:
        payload["sha"] = sha
        
    r = requests.put(url, headers=gh_headers(), json=payload)
    if r.status_code >= 300:
        raise RuntimeError(f"Upload {path} failed: {r.status_code} {r.text}")


def enable_pages(owner, repo):
    """Enables GitHub Pages for a repository."""
    url = f"{GITHUB_API}/repos/{owner}/{repo}/pages"
    payload = {"source": {"branch": "main", "path": "/"}}
    headers = gh_headers()
    headers["Accept"] = "application/vnd.github.switcheroo-preview+json"
    r = requests.post(url, headers=headers, json=payload)
    if r.status_code >= 300 and r.status_code != 409: # 409 means it might already be enabled
        requests.put(url, headers=headers, json=payload)


def latest_commit(owner, repo):
    """Gets the SHA of the latest commit on the main branch."""
    r = requests.get(f"{GITHUB_API}/repos/{owner}/{repo}/commits/main", headers=gh_headers())
    if r.status_code >= 300:
        return "unknown"
    return r.json()["sha"]


def generate_files_via_aipipe(brief):
    """Generates web app files using the AIPipe API."""
    if not APIPIPE_KEY:
        raise RuntimeError("Missing APIPIPE_API_KEY secret.")

    client = OpenAI(api_key=APIPIPE_KEY, base_url="https://aipipe.org/openrouter/v1")
    
    prompt = f"You are an expert web developer. Create a small, self-contained web app (HTML, JS, CSS) that fulfills this brief: {brief}. Respond ONLY in valid JSON format with three keys: `index_html`, `script_js`, `style_css`. Do not add any text before or after the JSON object."
    
    completion = client.chat.completions.create(
        model="openai/gpt-4.1-nano",
        messages=[
            {"role": "system", "content": "You write production-ready HTML, CSS, and JS code and respond in pure JSON."},
            {"role": "user", "content": prompt}
        ],
        max_tokens=2048,
        temperature=0.7,
        response_format={"type": "json_object"}
    )
    content = completion.choices[0].message.content
    
    try:
        result = json.loads(content)
    except json.JSONDecodeError:
        log(f"Failed to parse LLM response as JSON. Content: {content}")
        result = {"index_html": content, "script_js": "", "style_css": ""}

    html_content = result.get("index_html", "<h1>Error</h1><p>Failed to generate content.</p>")
    js_content = result.get("script_js", "")
    css_content = result.get("style_css", "")
    
    full_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Generated App</title>
    <style>{css_content}</style>
</head>
<body>
{html_content}
    <script>{js_content}</script>
</body>
</html>"""

    return {"index.html": full_html}


def deploy(json_input):
    """Main function to handle the deployment request."""
    try:
        data = json.loads(json_input)
        log("Received request")
        
        required_fields = ["email", "secret", "task", "nonce", "evaluation_url"]
        for f in required_fields:
            if f not in data:
                return json.dumps({"status": "error", "message": f"Missing field: {f}"})
                
        if data["secret"] != SECRET_KEY:
            return json.dumps({"status": "error", "message": "Invalid secret key."})
            
        brief = data.get("brief", "Create a simple hello world page.")
        task = data["task"]
        round_num = data.get("round", 1)
        attachments = data.get("attachments", [])
        
        # --- Deterministic Repo Naming for Updates ---
        task_slug = task.lower().replace(' ', '-')
        stable_id = hashlib.sha256(f"{data['email']}{task}".encode()).hexdigest()[:8]
        repo_name = f"{task_slug}-{stable_id}"
        
        owner = get_github_user()
        repo = get_repo(owner, repo_name)

        if repo is None:
            if round_num > 1:
                return json.dumps({"status": "error", "message": f"Repo '{repo_name}' not found for a round 2 update."})
            log(f"Repo '{repo_name}' not found. Creating it.")
            desc = f"Auto-generated repo for task: {task}"
            repo = create_repo(repo_name, desc)
            enable_pages(owner, repo_name)
        else:
            log(f"Found existing repo '{repo_name}'. Updating it.")

        repo_url = repo["html_url"]

        if attachments:
            brief += "\n\nThis app should use the following attachments:"
            for att in attachments:
                brief += f"\n- {att.get('name', 'file')}"

        files = generate_files_via_aipipe(brief)
        
        for att in attachments:
            try:
                name = att.get("name", "file.txt")
                uri = att.get("url", "")
                if uri.startswith("data:"):
                    header, b64data = uri.split(",", 1)
                    content = base64.b64decode(b64data).decode(errors="ignore")
                    files[name] = content
            except Exception as e:
                log(f"Attachment decode failed for '{name}': {e}")
                
        for path, content in files.items():
            upload_file(owner, repo_name, path, content, f"Update {path} for round {round_num}")
            
        readme = f"# {task}\n\nRound: {round_num}\n\nBrief:\n{brief}\n"
        license_text = f"MIT License\n\nCopyright (c) {time.localtime().tm_year} {AUTHOR}\n\n..."

        upload_file(owner, repo_name, "README.md", readme, "Update README")
        upload_file(owner, repo_name, "LICENSE", license_text, "Update LICENSE")
        
        pages_url = f"https://{owner}.github.io/{repo_name}/"
        
        time.sleep(5) 
        sha = latest_commit(owner, repo_name)
        
        payload = {
            "email": data["email"], "task": task, "round": round_num, "nonce": data["nonce"], 
            "repo_url": repo_url, "commit_sha": sha, "pages_url": pages_url
        }
        
        # --- Non-blocking notification to avoid timeouts ---
        def notify_evaluation_url(url, json_payload):
            """Sends a POST request in a separate thread."""
            try:
                # Increased timeout for safety, though it won't block the main response.
                requests.post(url, json=json_payload, timeout=20)
                log(f"Successfully notified evaluation URL: {url}")
            except requests.exceptions.RequestException as e:
                log(f"Notify evaluation URL failed in background thread: {e}")

        # Start the notification in a background thread
        notification_thread = threading.Thread(
            target=notify_evaluation_url,
            args=(data["evaluation_url"], payload)
        )
        notification_thread.start()
            
        return json.dumps({"status": "success", "repo_url": repo_url, "pages_url": pages_url, "commit_sha": sha})

    except Exception as e:
        log(traceback.format_exc())
        return json.dumps({"status": "error", "message": str(e)})

# --- Gradio Interface ---
iface = gr.Interface(
    fn=deploy,
    inputs=gr.Textbox(lines=20, label="Paste JSON request here"),
    outputs="json",
    title="LLM App Deployer API (via AIPipe)",
    description="Receives JSON, uses AIPipe-compatible OpenAI client to generate HTML/JS/CSS, creates/updates a GitHub repo, and notifies evaluation URL.",
    api_name="predict",
    flagging_options=None 
)

if __name__ == "__main__":
    iface.launch(
        server_name="0.0.0.0", 
        server_port=int(os.environ.get("PORT", 7860)),
        ssr_mode=False  # Disable experimental SSR for API stability
    )

