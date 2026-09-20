import uvicorn
from config import settings

if __name__ == "__main__":
    print(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    print(f"Control Dashboard: http://localhost:{settings.PORT}")
    print(f"API Docs: http://localhost:{settings.PORT}/docs")
    uvicorn.run("api.server:app", host=settings.HOST, port=settings.PORT, reload=settings.DEBUG)
