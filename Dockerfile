# 1. Get a lightweight Linux machine with Python pre-installed
FROM python:3.11-slim

# 2. Set the working directory inside the container
WORKDIR /app

# 3. Copy just the requirements first (Docker caches this step to build faster later)
COPY requirements.txt .

# 4. Install your Python packages
RUN pip install --no-cache-dir -r requirements.txt

# 5. Copy the rest of your actual code into the container
COPY . .

# 6. The Command: Run migrations first, then start the server
# We use ${PORT:-8000} so Railway can inject its own port dynamically
CMD ["sh", "-c", "alembic upgrade head && uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}"]