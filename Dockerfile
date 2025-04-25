FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create a non-root user to run the application
RUN useradd -m appuser
USER appuser

# Expose port
EXPOSE 6666

# Run the application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "6666"]
