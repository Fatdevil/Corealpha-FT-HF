import importlib
import os
import pathlib
import re
import sys


REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]


def ensure_packaged_modules():
    """Make packaged app archives importable."""

    for zip_path in REPO_ROOT.glob("*.zip"):
        if zip_path.suffix != ".zip":
            continue
        if str(zip_path) not in sys.path:
            sys.path.insert(0, str(zip_path))


def find_fastapi_app():
    repo = REPO_ROOT
    candidates = []
    for py in repo.rglob("*.py"):
        try:
            text = py.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        if "FastAPI(" in text:
            m = re.search(r"(?m)^\s*([a-zA-Z_]\w*)\s*=\s*FastAPI\(", text)
            if m:
                varname = m.group(1)
                module = (
                    py.relative_to(repo).with_suffix("").as_posix().replace("/", ".")
                )
                candidates.append((module, varname))
    for module, varname in candidates:
        mod = importlib.import_module(module)
        app = getattr(mod, varname, None)
        # Late import to avoid hard dep when scanning
        from fastapi import FastAPI  # type: ignore

        if isinstance(app, FastAPI):
            return module, varname
    return None, None


def main():
    # Allow explicit override: APP_MODULE="path.to.module:appvar"
    override = os.getenv("APP_MODULE")
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))
    reload_opt = os.getenv("UVICORN_RELOAD", "false").lower() == "true"

    ensure_packaged_modules()

    if override:
        module, var = override.split(":")
    else:
        module, var = find_fastapi_app()
        if not module:
            print(
                "No FastAPI app found. Set APP_MODULE='pkg.module:app'", file=sys.stderr
            )
            sys.exit(1)

    import uvicorn  # type: ignore

    uvicorn.run(
        f"{module}:{var}", host=host, port=port, reload=reload_opt, log_level="info"
    )


if __name__ == "__main__":
    main()
