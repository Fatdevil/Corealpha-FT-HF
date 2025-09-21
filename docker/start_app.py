import os
import sys


def main():
    override = os.getenv("APP_MODULE")
    env = os.getenv("ENV", "dev").lower()
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))
    reload_opt = os.getenv("UVICORN_RELOAD", "false").lower() == "true"

    if env == "prod" and not override:
        print("ENV=prod kräver APP_MODULE='pkg.module:app'", file=sys.stderr)
        sys.exit(1)

    if override:
        module, var = override.split(":")
    else:
        module, var = "corealpha_adapter.app", "app"

    import uvicorn

    uvicorn.run(f"{module}:{var}", host=host, port=port, reload=reload_opt, log_level="info")


if __name__ == "__main__":
    main()
