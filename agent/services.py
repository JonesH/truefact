import os
import asyncio
import logging
from typing import Dict, Any, Optional
from masumi.config import Config
from masumi.payment import Payment, Amount

logger = logging.getLogger("masumi-agent.services")

async def execute_ai_task(input_data: Dict[str, str]) -> Dict[str, Any]:
    """Execute an AI task based on the input data"""
    logger.info(f"Executing AI task with input: {input_data}")
    
    # Simulate AI processing time
    await asyncio.sleep(2)
    
    text_input = input_data.get("text", "No text provided")
    
    # Simple dummy processing
    if "story" in text_input.lower():
        result = f"Once upon a time, there was a {text_input.split()[-1]}. "
        result += "They lived in a world of wonder and amazement. "
        result += "Every day brought new adventures and discoveries. "
        result += "And they lived happily ever after."
    elif "summary" in text_input.lower():
        result = f"This is a summary about {text_input.split()[-1]}. "
        result += "It contains the most important points in a concise format."
    else:
        result = f"Processed result for: {text_input}"
        
    return {"raw": result}

async def create_payment_request(job_id: str, input_data: Dict[str, str], 
                                identifier_from_purchaser: str) -> Optional[Dict[str, Any]]:
    """Create a payment request using Masumi Payment Service"""
    try:
        config = Config(
            payment_service_url=os.getenv("MASUMI_PAYMENT_BASE_URL"),
            payment_api_key=os.getenv("MASUMI_PAYMENT_TOKEN"),
            registry_api_key=os.getenv("MASUMI_REGISTRY_TOKEN")
        )
        
        payment = Payment(
            agent_identifier=os.getenv("AGENT_IDENTIFIER"),
            amounts=[Amount(amount="1000000", unit="lovelace")],
            config=config,
            network=os.getenv("MASUMI_NETWORK", "Preprod"),
            identifier_from_purchaser=identifier_from_purchaser,
            input_data=str(input_data)
        )
        
        result = await payment.create_payment_request()
        return result["data"] if "data" in result else None
    except Exception as e:
        logger.error(f"Payment request creation failed: {e}", exc_info=True)
        return None

async def handle_payment_status(job_id: str, jobs: Dict[str, Dict[str, Any]]) -> None:
    """Monitor payment status and execute task when payment is confirmed"""
    try:
        if job_id not in jobs or not jobs[job_id].get("payment_id"):
            logger.error(f"Invalid job or missing payment ID for {job_id}")
            return

        # Configure Masumi payment
        config = Config(
            payment_service_url=os.getenv("MASUMI_PAYMENT_BASE_URL"),
            payment_api_key=os.getenv("MASUMI_PAYMENT_TOKEN"),
            registry_api_key=os.getenv("MASUMI_REGISTRY_TOKEN")
        )

        blockchain_id = jobs[job_id].get("payment_id")
        logger.info(f"Monitoring payment for job {job_id} with ID {blockchain_id}")

        # Create payment instance
        payment = Payment(
            agent_identifier=os.getenv("AGENT_IDENTIFIER"),
            config=config,
            network=os.getenv("MASUMI_NETWORK", "Preprod"),
            identifier_from_purchaser=jobs[job_id]["identifier_from_purchaser"],
            blockchain_identifier=blockchain_id
        )

        # Define payment callback
        async def on_payment_complete(payment_id):
            logger.info(f"Payment {payment_id} completed for job {job_id}")
            jobs[job_id]["status"] = "running"
            jobs[job_id]["payment_status"] = "completed"

            # Execute the AI task
            result = await execute_ai_task(jobs[job_id]["input_data"])

            # Update job status
            jobs[job_id]["status"] = "completed"
            jobs[job_id]["result"] = result

            # Complete payment with result hash
            result_hash = str(hash(str(result)))
            await payment.complete_payment(blockchain_id, result_hash)

            logger.info(f"Task completed for job {job_id}")

        # Start monitoring payment status
        await payment.start_status_monitoring(
            callback=on_payment_complete,
            interval_seconds=10
        )

    except Exception as e:
        logger.error(f"Error monitoring payment for job {job_id}: {e}", exc_info=True)
        jobs[job_id]["status"] = "failed"
        jobs[job_id]["error"] = str(e)