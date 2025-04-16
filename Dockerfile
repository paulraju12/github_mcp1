FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy and verify requirements.txt
COPY requirements.txt .
RUN test -f requirements.txt || (echo "requirements.txt not found" && exit 1)
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY community_github_mcp/ ./community_github_mcp/

# Set Python path
ENV PYTHONPATH="/app"

# Expose port
EXPOSE 3005

# Run the application
CMD ["python", "community_github_mcp/server.py"]