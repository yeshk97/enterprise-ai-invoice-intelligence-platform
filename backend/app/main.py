from fastapi import FastAPI

# Create FastAPI application instance
app = FastAPI(
    title="Enterprise AI Invoice Intelligence Platform",
    description="Backend API for invoice intake, AI extraction, validation, RAG, agents, and workflow automation.",
    version="0.1.0",
)


@app.get("/")
def root():
    """
    Root endpoint.

    This confirms the backend API is reachable.
    """
    return {
        "message": "Welcome to the Enterprise AI Invoice Intelligence Platform API"
    }


@app.get("/health")
def health_check():
    """
    Health check endpoint.

    In production, health check endpoints are used by load balancers,
    cloud platforms, and monitoring tools to confirm the service is running.
    """
    return {
        "status": "success",
        "message": "Enterprise AI Invoice Intelligence Platform backend is running"
    }