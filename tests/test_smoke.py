import importlib
import pathlib
import re
from fastapi import FastAPI
from fastapi.testclient import TestClient

def find_app():
    repo = pathlib.Path(__file__).resolve().parents[1]
    candidates = []
    for py in repo.rglob("*.py"):
        text = py.read_text(encoding="utf-8", errors="ignore")
        if "FastAPI(" in text:
            m = re.search(r'(?m)^\s*([a-zA-Z_]\w*)\s*=\s*FastAPI\(', text)
            if m:
                app_var = m.group(1)
                module_path = py.relative_to(repo).with_suffix("").as_posix().replace("/", ".")
                candidates.append((module_path, app_var))
    for module_path, app_var in candidates:
        mod = importlib.import_module(module_path)
        app = getattr(mod, app_var, None)
        if isinstance(app, FastAPI):
            return app
    raise RuntimeError("No FastAPI app found")

def test_app_imports_and_root_status():
    app = find_app()
    client = TestClient(app)
    resp = client.get("/")
    assert resp.status_code in (200, 404)  # 404 ok om root-route saknas
