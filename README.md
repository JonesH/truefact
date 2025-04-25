# Masumi Agent Demo

A demonstration of a Masumi-compatible agent implemented with FastAPI.

## Overview

This project demonstrates how to implement the required endpoints for a Masumi agent:

- `/start_job` - Start a new job with payment integration
- `/status` - Check the status of a job
- `/input_schema` - Get the input schema for the agent
- `/availability` - Check if the agent is available
- `/health` - Simple health check endpoint

## Getting Started

### Prerequisites

- Python 3.10+
- pip

### Installation

1. Clone this repository:
   ```bash
   git clone https://github.com/your-username/masumi-agent-demo.git
   cd masumi-agent-demo
   ```

2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Copy the example environment file and adjust settings:
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

### Running the Agent

Start the FastAPI server:

```bash
uvicorn main:app --reload
```

The agent will be available at http://localhost:8000 with API documentation at http://localhost:8000/docs.

## Testing

Run tests with pytest:

```bash
pytest
```

## Masumi Integration

To fully integrate with the Masumi network:

1. Register your agent with the Masumi Registry Service
2. Configure the Masumi Payment Service
3. Update the `.env` file with your agent's credentials

## License

This project is licensed under the MIT License - see the LICENSE file for details.
