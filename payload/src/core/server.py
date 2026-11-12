#!/usr/bin/env python3
"""NEXUS-OS local control server. Python standard library only."""
from __future__ import annotations
import json, os, platform, shutil, socket, subprocess, time
from datetime import datetime
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
from urllib.parse import urlparse, parse_qs, unquote

ROOT = Path(__file__).resolve().parents[2]
WEB = ROOT / "src" / "interface" / "web"
HOST, PORT = "127.0.0.1", int(os.environ.get("NEXUS_PORT", "8080"))
MAX_BODY = 2 * 1024 * 1024
SAFE_COMMANDS = {"pwd", "ls", "whoami", "date", "python --version", "git status", "du -sh ."}

def safe_path(raw: str = "") -> Path:
    candidate = (ROOT / raw.lstrip("/")).resolve()
    if candidate != ROOT and ROOT not in candidate.parents:
        raise ValueError("Chemin hors de l'espace NEXUS interdit.")
    return candidate

def json_bytes(data):
    return json.dumps(data, ensure_ascii=False).encode("utf-8")

class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(WEB), **kwargs)

    def log_message(self, fmt, *args):
        print("[NEXUS]", fmt % args)

    def send_json(self, data, status=200):
        payload = json_bytes(data)
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(payload)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(payload)

    def body(self):
        size = int(self.headers.get("Content-Length", "0"))
        if size > MAX_BODY:
            raise ValueError("Fichier trop volumineux (limite 2 Mo par requête).")
        raw = self.rfile.read(size) if size else b"{}"
        return json.loads(raw.decode("utf-8"))

    def do_GET(self):
        parsed = urlparse(self.path)
        path, qs = parsed.path, parse_qs(parsed.query)
        try:
            if path == "/api/status":
                usage = shutil.disk_usage(ROOT)
                self.send_json({
                    "name": "NEXUS-OS", "version": "0.3.0", "status": "online",
                    "time": datetime.now().astimezone().isoformat(timespec="seconds"),
                    "python": platform.python_version(), "platform": platform.platform(),
                    "root": str(ROOT), "disk_free": usage.free, "disk_total": usage.total,
                    "uptime_note": "Serveur local actif"
                }); return
            if path == "/api/files":
                rel = qs.get("path", [""])[0]
                folder = safe_path(rel)
                if not folder.exists() or not folder.is_dir():
                    self.send_json({"error": "Dossier introuvable."}, 404); return
                items = []
                for p in sorted(folder.iterdir(), key=lambda x: (not x.is_dir(), x.name.lower())):
                    try:
                        st = p.stat()
                        items.append({"name": p.name, "path": str(p.relative_to(ROOT)),
                                      "type": "folder" if p.is_dir() else "file",
                                      "size": st.st_size, "modified": datetime.fromtimestamp(st.st_mtime).astimezone().isoformat(timespec="minutes")})
                    except OSError: pass
                self.send_json({"path": str(folder.relative_to(ROOT)) if folder != ROOT else "",
                                "parent": str(folder.parent.relative_to(ROOT)) if folder != ROOT else None,
                                "items": items}); return
            if path == "/api/read":
                p = safe_path(qs.get("path", [""])[0])
                if not p.is_file(): self.send_json({"error": "Fichier introuvable."}, 404); return
                if p.stat().st_size > MAX_BODY: self.send_json({"error": "Fichier trop volumineux pour l'éditeur."}, 413); return
                try: content = p.read_text(encoding="utf-8")
                except UnicodeDecodeError: self.send_json({"error": "Fichier binaire : aperçu texte impossible."}, 415); return
                self.send_json({"path": str(p.relative_to(ROOT)), "content": content}); return
            if path == "/api/health":
                self.send_json({"ok": True, "service": "nexus-core"}); return
            return super().do_GET()
        except (ValueError, OSError, json.JSONDecodeError) as e:
            self.send_json({"error": str(e)}, 400)

    def do_POST(self):
        path = urlparse(self.path).path
        try:
            data = self.body()
            if path == "/api/files/create":
                parent = safe_path(data.get("path", ""))
                name = Path(data.get("name", "")).name
                if not name or name in {".", ".."}: raise ValueError("Nom invalide.")
                target = parent / name
                if target.exists(): raise ValueError("Un élément porte déjà ce nom.")
                if data.get("type") == "folder": target.mkdir(parents=False)
                else: target.touch()
                self.send_json({"ok": True, "path": str(target.relative_to(ROOT))}); return
            if path == "/api/files/save":
                target = safe_path(data.get("path", ""))
                if not target.is_file(): raise ValueError("Fichier introuvable.")
                content = data.get("content", "")
                if not isinstance(content, str): raise ValueError("Contenu invalide.")
                target.write_text(content, encoding="utf-8")
                self.send_json({"ok": True, "saved": str(target.relative_to(ROOT))}); return
            if path == "/api/files/rename":
                source = safe_path(data.get("path", ""))
                name = Path(data.get("name", "")).name
                if not source.exists() or not name: raise ValueError("Source ou nom invalide.")
                target = source.with_name(name)
                if target.exists(): raise ValueError("La destination existe déjà.")
                source.rename(target)
                self.send_json({"ok": True, "path": str(target.relative_to(ROOT))}); return
            if path == "/api/files/delete":
                target = safe_path(data.get("path", ""))
                if target == ROOT: raise ValueError("Suppression de la racine interdite.")
                if not target.exists(): raise ValueError("Élément introuvable.")
                if target.is_dir(): shutil.rmtree(target)
                else: target.unlink()
                self.send_json({"ok": True}); return
            if path == "/api/terminal":
                command = data.get("command", "").strip()
                if command not in SAFE_COMMANDS:
                    self.send_json({"error": "Commande non autorisée. Utilise Aide pour voir la liste."}, 403); return
                result = subprocess.run(command, shell=True, cwd=ROOT, capture_output=True, text=True, timeout=8)
                self.send_json({"command": command, "output": (result.stdout + result.stderr).strip(), "code": result.returncode}); return
            self.send_json({"error": "Route inconnue."}, 404)
        except Exception as e:
            self.send_json({"error": str(e)}, 400)

def main():
    server = ThreadingHTTPServer((HOST, PORT), Handler)
    print(f"NEXUS-OS 0.3.0 — http://{HOST}:{PORT}")
    print(f"Espace de travail : {ROOT}")
    try: server.serve_forever()
    except KeyboardInterrupt: print("\nArrêt NEXUS-OS")
    finally: server.server_close()

if __name__ == "__main__":
    main()
