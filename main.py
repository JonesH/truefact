import os
import uuid
import logging
from typing import Dict, Any
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from agent.models import StartJobRequest, JobStatus, InputSchema, AgentAvailability, HealthCheck
from agent.services import handle_payment_status

# Load environment variables
load_dotenv(override=True)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("masumi-agent")

# Initialize FastAPI app
app = FastAPI(
    title="Truefact AI Agent API",
    description="API for running AI agent tasks with Masumi payment integration",
    version="1.0.0",
    servers=[{"url": f"https://{os.getenv('SERVER_NAME', 6666)}"}]
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
async def start_job(data: StartJobRequest) -> Dict[str, Any]:
    """Start a new job and create a payment request."""
    logger.info(f"Received job request with input: {data.input_data}")
    
    try:
        # Generate a unique job ID
        job_id = str(uuid.uuid4())
        agent_identifier = os.getenv("AGENT_IDENTIFIER", "demo-agent")
        
        # For demo purposes, we'll just simulate payment
        # In a real implementation, you would use:
        # from masumi.config import Config
        # from masumi.payment import Payment
        
        # Initialize jobs dict with status
        jobs[job_id] = {
            "status": "awaiting_payment",
            "payment_status": "pending",
            "payment_id": f"demo-payment-{job_id}",
            "input_data": data.input_data,
            "result": None,
            "identifier_from_purchaser": data.identifier_from_purchaser
        }
        
        # Simulate payment with delayed execution
        # In real implementation, use payment callback
        import asyncio
        asyncio.create_task(handle_payment_status(job_id, jobs))
        
        # Return response in required format
        return {
            "status": "success",
            "job_id": job_id,
            "blockchainIdentifier": f"demo-blockchain-{job_id}",
            "submitResultTime": "1650000000",
            "unlockTime": "1650001000",
            "externalDisputeUnlockTime": "1650002000",
            "agentIdentifier": agent_identifier,
            "sellerVkey": os.getenv("SELLER_VKEY", "demo-vkey"),
            "identifierFromPurchaser": data.identifier_from_purchaser,
            "input_hash": "demo-input-hash"
        }
    except Exception as e:
        logger.error(f"Error in start_job: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=400,
            detail=f"Error: {str(e)}"
        )

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
    uvicorn.run(app, host="0.0.0.0", port=os.getenv("PORT", 6666))
