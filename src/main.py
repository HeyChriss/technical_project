"""Main FastAPI application."""

from fastapi import FastAPI
from src.api.routes import router


app = FastAPI(
    title="Multi-Vehicle Search API"
)

# Include API routes
app.include_router(router)


@app.get("/health")
async def health_check():
    """Health check endpoint.
    
    Returns:
        Status message
    """
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

