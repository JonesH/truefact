import os
import uuid
import logging

import httpx
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from masumi.config import Config
from masumi.payment import Payment, Amount
from agent.models import StartJobRequest, JobStatus, InputSchema, AgentAvailability, HealthCheck, StartJobResponse, Amount as AmountModel
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

# Initialize Masumi Configuration
masumi_config = Config(
    payment_service_url=os.getenv("MASUMI_PAYMENT_BASE_URL"),
    payment_api_key=os.getenv("MASUMI_PAYMENT_TOKEN")
)

# In-memory job store (replace with a database in production)
jobs = {}
payment_instances = {}

# Payment callback handler
async def handle_payment_status(job_id: str, payment_id: str) -> None:
    """Executes AI task after payment confirmation"""
    try:
        logger.info(f"Payment {payment_id} completed for job {job_id}, executing task...")
        
        # Update job status to running
        jobs[job_id]["status"] = "running"
        logger.info(f"Processing input data: {jobs[job_id]['input_data']}")

        # Execute the AI task 
        result = await execute_ai_task(jobs[job_id]["input_data"]["text"], job_id=job_id)
        logger.info(f"AI task completed for job {job_id}")
        
        # Mark payment as completed on Masumi
        result_hash = str(hash(str(result)))[:32]
        await payment_instances[job_id].complete_payment(payment_id, result_hash)
        logger.info(f"Payment completed for job {job_id}")

        # Update job status
        jobs[job_id]["status"] = "completed"
        jobs[job_id]["payment_status"] = "completed"
        jobs[job_id]["result"] = result

        # Stop monitoring payment status
        if job_id in payment_instances:
            payment_instances[job_id].stop_status_monitoring()
            del payment_instances[job_id]
    except Exception as e:
        logger.error(f"Error processing payment {payment_id} for job {job_id}: {e}", exc_info=True)
        jobs[job_id]["status"] = "failed"
        jobs[job_id]["error"] = str(e)
        
        # Still stop monitoring to prevent repeated failures
        if job_id in payment_instances:
            payment_instances[job_id].stop_status_monitoring()
            del payment_instances[job_id]

async def execute_ai_task(input_text: str, job_id: str) -> str:
    """Execute the AI task with the given input"""
    # In a real implementation, this would call your AI service
    # For now, we'll return a simple confirmation
    logger.info(f"Processing AI task with input: {input_text[:100]}...")
    webhook_url = os.getenv("N8N_WEBHOOK_URL")

    async with httpx.AsyncClient() as client:
        response = await client.post(webhook_url, json=dict(text=input_text, job_id=job_id))
        response.raise_for_status()  # abort on HTTP errors
        return response.text


# Implement required endpoints
@app.post("/start_job")
async def start_job(data: StartJobRequest) -> StartJobResponse:
    """Start a new job and create a payment request."""
    try:
        job_id = str(uuid.uuid4())
        agent_identifier = os.getenv("AGENT_IDENTIFIER", "demo-agent")

        # Log input (truncated if necessary)
        input_text = data.input_data.get("text", "")
        truncated_input = f"{input_text[:100]}..." if len(input_text) > 100 else input_text
        logger.info(f"Received job request with input: '{truncated_input}'")

        # Define payment amounts
        payment_amount = int(os.getenv("PAYMENT_AMOUNT", "10000000"))
        payment_unit = os.getenv("PAYMENT_UNIT", "lovelace")
        
        # Create payment amount objects
        amounts = [Amount(amount=payment_amount, unit=payment_unit)]
        logger.info(f"Using payment amount: {payment_amount} {payment_unit}")
        
        # Create a payment request using Masumi
        network = os.getenv("MASUMI_NETWORK", "Preprod")
        payment = Payment(
            agent_identifier=agent_identifier,
            amounts=amounts,
            config=masumi_config,
            network=network,
            identifier_from_purchaser=data.identifier_from_purchaser,
            input_data=data.input_data
        )
        
        logger.info("Creating payment request...")
        payment_result = await payment.create_payment_request()
        payment_id = payment_result["data"]["blockchainIdentifier"]
        payment.payment_ids.add(payment_id)
        logger.info(f"Created payment request with ID: {payment_id}")

        # Store job info (Awaiting payment)
        jobs[job_id] = {
            "status": "awaiting_payment",
            "payment_status": "pending",
            "payment_id": payment_id,
            "input_data": data.input_data,
            "result": None,
            "identifier_from_purchaser": data.identifier_from_purchaser
        }
        
        # Create payment callback
        async def payment_callback(payment_id: str) -> None:
            await handle_payment_status(job_id, payment_id)

        # Start monitoring the payment status
        payment_instances[job_id] = payment
        logger.info(f"Starting payment status monitoring for job {job_id}")
        await payment.start_status_monitoring(payment_callback)

        # Format amounts for response
        amount_list = [AmountModel(amount=amt.amount, unit=amt.unit) for amt in amounts]
        
        # Return conformant response
        return StartJobResponse(
            status="success",
            job_id=job_id,
            blockchainIdentifier=payment_result["data"]["blockchainIdentifier"],
            submitResultTime=payment_result["data"]["submitResultTime"],
            unlockTime=payment_result["data"]["unlockTime"],
            externalDisputeUnlockTime=payment_result["data"]["externalDisputeUnlockTime"],
            agentIdentifier=agent_identifier,
            sellerVkey=os.getenv("SELLER_VKEY", ""),
            identifierFromPurchaser=data.identifier_from_purchaser,
            amounts=amount_list,
            input_hash=payment.input_hash
        )
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

    # Check latest payment status if payment instance exists
    if job_id in payment_instances:
        try:
            status = await payment_instances[job_id].check_payment_status()
            job["payment_status"] = status.get("data", {}).get("status", "unknown")
            logger.info(f"Updated payment status for job {job_id}: {job['payment_status']}")
        except Exception as e:
            logger.error(f"Error checking payment status: {e}", exc_info=True)
            job["payment_status"] = "error"

    result = job.get("result")

    return JobStatus(
        job_id=job_id,
        status=job["status"],
        payment_status=job["payment_status"],
        result=result
    )

@app.get("/input_schema")
async def input_schema() -> str:
    """Get the input schema for the agent."""
    logger.info("Input schema requested")
    return InputSchema.model_json_schema()


@app.get("/availability")
async def check_availability() -> AgentAvailability:
    """Check if the agent is available."""
    logger.info("Availability check")
    return AgentAvailability(
        status="available",
        agentIdentifier=os.getenv("AGENT_IDENTIFIER", "demo-agent"),
        message="The server is running smoothly."
    )

@app.get("/health")
async def health() -> HealthCheck:
    """Get the health status of the agent."""
    logger.info("Health check")
    return HealthCheck(
        status="healthy"
    )

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 6666))
    uvicorn.run(app, host="0.0.0.0", port=port)
