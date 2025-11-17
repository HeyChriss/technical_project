"""Main FastAPI application."""

from fastapi import FastAPI
from src.api.routes import router


app = FastAPI(
    title="Multi-Vehicle Search API"
)

# Include API routes
app.include_router(router)


@app.get("/")
async def root():
    """Root endpoint with API information.
    
    Returns:
        API information and usage instructions
    """
    return {
        "message": "Multi-Vehicle Search API",
        "description": "Search for storage locations that can accommodate multiple vehicles",
        "endpoints": {
            "POST /": "Search for vehicle storage locations",
            "GET /health": "Health check endpoint",
            "GET /docs": "Interactive API documentation (Swagger UI)",
        },
        "usage": {
            "method": "POST",
            "url": "/",
            "content_type": "application/json",
            "example_request": [
                {
                    "length": 10,
                    "quantity": 1
                },
                {
                    "length": 20,
                    "quantity": 2
                }
            ],
            "example_curl": 'curl -X POST "https://multi-vehicle-search-api.onrender.com/" -H "Content-Type: application/json" -d \'[{"length": 10, "quantity": 1}]\''
        }
    }


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

