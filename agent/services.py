import asyncio
import logging
from typing import Dict, Any

logger = logging.getLogger("masumi-agent.services")

async def execute_ai_task(input_data: Dict[str, str]) -> Dict[str, Any]:
    """
    Execute an AI task based on the input data.
    
    In a real implementation, this would call your model or API.
    For this example, we just simulate processing.
    
    Args:
        input_data: The input data for the AI task
        
    Returns:
        Dictionary containing the result
    """
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

async def handle_payment_status(job_id: str, jobs: Dict[str, Dict[str, Any]]) -> None:
    """
    Handle payment status updates.
    
    In a real implementation, this would monitor the blockchain for payment.
    For this example, we just simulate the process.
    
    Args:
        job_id: The ID of the job to handle
        jobs: The job store
    """
    try:
        logger.info(f"Payment for job {job_id} received, executing task...")
        
        # Simulate payment confirmation delay
        await asyncio.sleep(3)
        
        # Update job status to running
        jobs[job_id]["status"] = "running"
        jobs[job_id]["payment_status"] = "completed"
        
        # Execute the AI task
        result = await execute_ai_task(jobs[job_id]["input_data"])
        
        # In a real implementation, you would mark payment as completed:
        # await payment_instances[job_id].complete_payment(payment_id, result)
        
        # Update job status
        jobs[job_id]["status"] = "completed"
        jobs[job_id]["result"] = result
        
        logger.info(f"Task completed for job {job_id}")
        
    except Exception as e:
        logger.error(f"Error processing task for job {job_id}: {str(e)}", exc_info=True)
        jobs[job_id]["status"] = "failed"
        jobs[job_id]["error"] = str(e)
