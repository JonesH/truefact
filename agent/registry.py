import os
import logging
from masumi.config import Config
from masumi.registry import Agent
from agent.config import update_env_file

logger = logging.getLogger("masumi-agent.registry")

async def ensure_agent_registration() -> bool:
    """Check if agent exists in Masumi Registry, register if not"""
    logger.info("Verifying agent registration")
    
    try:
        config = Config(
            payment_service_url=os.getenv("MASUMI_PAYMENT_BASE_URL"),
            payment_api_key=os.getenv("MASUMI_PAYMENT_TOKEN"),
            registry_api_key=os.getenv("MASUMI_REGISTRY_TOKEN")
        )
        
        network = os.getenv("MASUMI_NETWORK", "Preprod")
        agent_identifier = os.getenv("AGENT_IDENTIFIER")
        
        agent = Agent(
            name="Truefact AI Agent",
            config=config,
            description="AI agent that generates factual responses",
            example_output=[{"url": f"https://{os.getenv('SERVER_NAME')}", "name": "factual_response", "mimeType": "application/json"}],
            tags=["AI", "Factual", "Truefact"],
            api_base_url=f"https://{os.getenv('SERVER_NAME')}",
            author_name="TrueFact",
            author_contact="contact@truefact.ai",
            author_organization="TrueFact AI",
            legal_privacy_policy="", legal_terms="", legal_other="",
            capability_name="factual_analysis",
            capability_version="1.0.0",
            requests_per_hour="100",
            pricing_unit="lovelace",
            pricing_quantity="1000000",
            network=network
        )
        
        # Check if already registered
        wallet_vkey = os.getenv("SELLER_VKEY")
        
        if agent_identifier and wallet_vkey:
            # Using agent identifier to check registration
            status = await agent.check_registration_status(wallet_vkey)
            if status.get("exists", False):
                logger.info("Agent already registered")
                return True
            else:
                logger.info("Agent not registered, registering now...")
        
        # Register the agent
        result = await agent.register()
        
        # Update environment variables with registration data
        env_updates = {}
        
        if vkey := result.get("vkey"):
            os.environ["SELLER_VKEY"] = vkey
            env_updates["SELLER_VKEY"] = vkey
            logger.info(f"Updated SELLER_VKEY to {vkey}")
        
        if agent_id := result.get("agentIdentifier"):
            os.environ["AGENT_IDENTIFIER"] = agent_id
            env_updates["AGENT_IDENTIFIER"] = agent_id
            logger.info(f"Updated AGENT_IDENTIFIER to {agent_id}")
        
        # Persist changes to .env file
        if env_updates:
            update_env_file(env_updates)
            logger.info("Persisted agent registration data to .env file")
        
        logger.info("Agent registration successful")
        return True
        
    except Exception as e:
        logger.error(f"Agent registration failed: {e}", exc_info=True)
        return False


if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv(override=True)
    import asyncio
    asyncio.run(ensure_agent_registration())
