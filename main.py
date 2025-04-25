import os
import uuid
import logging
from typing import Dict, Any
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from agent.models import StartJobRequest, JobStatus, InputSchema, AgentAvailability, HealthCheck
from agent.registry import ensure_agent_registration

# Load environment variables
load_dotenv(override=True)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("masumi-agent")

# Define lifespan context manager for startup/shutdown events
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup logic
    logger.info("Starting Truefact AI Agent")
    registered = await ensure_agent_registration()
    logger.info(f"Agent registration status: {'Success' if registered else 'Failed'}")
    yield
    # Shutdown logic
    logger.info("Shutting down Truefact AI Agent")

# Initialize FastAPI app with lifespan
app = FastAPI(
    title="Truefact AI Agent API",
    description="API for running AI agent tasks with Masumi payment integration",
    version="1.0.0",
    servers=[{"url": f"https://{os.getenv('SERVER_NAME', 'localhost')}"}],
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory job store (replace with a database in production)
jobs = {}
payment_instances = {}



# Implement required endpoints
@app.post("/start_job")
async def start_job(data: StartJobRequest) -> dict[str, Any]:
    """Start a new job and create a payment request."""
    try:
        job_id = str(uuid.uuid4())
        agent_identifier = os.getenv("AGENT_IDENTIFIER", "demo-agent")

        # Log input (truncated if necessary)
        input_text = data.input_data.get("text", "")
        truncated_input = f"{input_text[:100]}..." if len(input_text) > 100 else input_text
        logger.info(f"Received job request with input: '{truncated_input}'")

        # Define payment amounts
        payment_amount = os.getenv("PAYMENT_AMOUNT", "10000000")
        payment_unit = os.getenv("PAYMENT_UNIT", "lovelace")
        amounts = [{"amount": payment_amount, "unit": payment_unit}]

        # TODO: fix this claude

        # Return conformant response
        return {
            "status": "success",
            "job_id": job_id,
            **payment_result,
            "identifierFromPurchaser": data.identifier_from_purchaser,
            "sellerVkey": os.getenv("SELLER_VKEY"),
            "amounts": amounts
        }
    except KeyError as e:
        logger.error(f"Missing required field: {e}", exc_info=True)
        raise HTTPException(
            status_code=400,
            detail="Missing required field in request schema"
        ) from e
    except Exception as e:
        logger.error(f"Error in start_job: {e}", exc_info=True)
        raise HTTPException(
            status_code=400,
            detail=f"Error: {e}"
        ) from e

@app.get("/status")
async def get_status(job_id: str = Query(..., description="The ID of the job to check")) -> JobStatus:
    """Get the status of a specific job."""
    logger.info(f"Checking status for job {job_id}")
    
    if job_id not in jobs:
        logger.warning(f"Job {job_id} not found")
        raise HTTPException(status_code=404, detail="Job not found")
    
    job = jobs[job_id]
    result = job.get("result")
    
    return {
        "job_id": job_id,
        "status": job["status"],
        "payment_status": job["payment_status"],
        "result": result
    }

@app.get("/input_schema")
async def input_schema() -> InputSchema:
    """Get the input schema for the agent."""
    logger.info("Input schema requested")
    return {
        "input_data": [
            {
                "id": "text",
                "type": "string",
                "name": "Text",
                "data": {
                    "description": "The text input for the AI task",
                    "placeholder": "Enter your task description here"
                }
            }
        ]
    }

@app.get("/availability")
async def check_availability() -> AgentAvailability:
    """Check if the agent is available."""
    logger.info("Availability check")
    return {
        "status": "available",
        "agentIdentifier": os.getenv("AGENT_IDENTIFIER", "demo-agent"),
        "message": "The server is running smoothly."
    }

@app.get("/health")
async def health() -> HealthCheck:
    """Get the health status of the agent."""
    logger.info("Health check")
    return {
        "status": "healthy"
    }

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 6666))
    uvicorn.run(app, host="0.0.0.0", port=port)
