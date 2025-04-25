from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field

class StartJobRequest(BaseModel):
    """
    Request model for starting a job.
    """
    identifier_from_purchaser: str = Field(..., description="Identifier provided by the purchaser")
    input_data: Dict[str, str] = Field(..., description="Input data for the job")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "identifier_from_purchaser": "example_purchaser_123",
                "input_data": {
                    "text": "Write a story about a robot learning to paint"
                }
            }
        }
    }

class JobStatus(BaseModel):
    """
    Response model for job status.
    """
    job_id: str
    status: str  # "awaiting_payment", "running", "completed", "failed"
    payment_status: str  # "pending", "completed", "error"
    result: Optional[Any] = None

class InputDataField(BaseModel):
    """
    Information about an input field.
    """
    id: str
    type: str
    name: str
    data: Dict[str, str]

class InputSchema(BaseModel):
    """
    Response model for input schema.
    """
    input_data: List[InputDataField]

class AgentAvailability(BaseModel):
    """
    Response model for agent availability.
    """
    status: str  # "available", "unavailable"
    agentIdentifier: str
    message: str

class HealthCheck(BaseModel):
    """
    Response model for health check.
    """
    status: str  # "healthy", "unhealthy"

class Amount(BaseModel):
    """
    Payment amount model.
    """
    amount: str
    unit: str

class StartJobResponse(BaseModel):
    """
    Response model for starting a job.
    """
    status: str
    job_id: str
    blockchainIdentifier: str
    submitResultTime: int
    unlockTime: int
    externalDisputeUnlockTime: int
    agentIdentifier: str
    sellerVkey: str
    identifierFromPurchaser: str
    amounts: List[Amount]
    input_hash: str
