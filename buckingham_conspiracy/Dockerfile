# Stage 1: Build the frontend for the custom component
FROM node:18-slim as builder

# Set the working directory for the frontend build
WORKDIR /app/components/st_musicxml_viewer/frontend

# Copy package.json and install dependencies to leverage Docker layer caching
COPY ./components/st_musicxml_viewer/frontend/package.json ./
# Use `ci` for reproducible builds if a lock file is present
RUN if [ -f package-lock.json ]; then npm ci; else npm install; fi

# Copy the rest of the frontend source code and build it
COPY ./components/st_musicxml_viewer/frontend/ .
RUN npm run build

# ---

# Stage 2: Build the final Python application image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    STREAMLIT_SERVER_PORT=8501 \
    STREAMLIT_SERVER_ADDRESS=0.0.0.0

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire application source code
COPY . .

# Copy the built frontend from the builder stage
COPY --from=builder /app/components/st_musicxml_viewer/frontend/build /app/components/st_musicxml_viewer/frontend/build

# Create a directory for persistent data if needed
RUN mkdir -p /app/data

# Expose the Streamlit port
EXPOSE 8501

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8501/_stcore/health || exit 1

# Run the Streamlit app
CMD ["streamlit", "run", "src/app.py", "--server.port=8501", "--server.address=0.0.0.0"]
