import os
import re
from typing import Dict, Any, Optional
from dotenv import load_dotenv

def update_env_file(updates: Dict[str, str]) -> bool:
    """Update .env file with new or changed values
    
    Args:
        updates: Dictionary of key-value pairs to update
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        env_path = ".env"
        
        # Read existing content
        if os.path.exists(env_path):
            with open(env_path, "r") as f:
                content = f.read()
        else:
            content = ""
            
        # Update each key-value pair
        for key, value in updates.items():
            # Skip if value is None or empty
            if not value:
                continue
                
            pattern = re.compile(f"^{key}=.*$", re.MULTILINE)
            replacement = f"{key}={value}"
            
            if pattern.search(content):
                # Replace existing entry
                content = pattern.sub(replacement, content)
            else:
                # Add new entry
                content += f"\n{replacement}"
        
        # Write updated content back
        with open(env_path, "w") as f:
            f.write(content)
            
        return True
    except Exception as e:
        print(f"Error updating .env file: {e}")
        return False