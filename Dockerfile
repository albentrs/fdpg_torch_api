FROM python:3.12-slim

WORKDIR /app/FDPG_torch_API

COPY resources ./resources


ADD jsnonSchema.py .
ADD torch_requests.py .
ADD main.py .

# Copy the requirements file to the working directory
COPY requirements.txt .

# Install the dependencies
RUN pip install -r requirements.txt

# Port für den Container freigeben
EXPOSE 8000

# Startbefehl für FastAPI mit Uvicorn
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]

# to bulid and publish
#docker build -t fdpg_torch_api .
#docker tag fdpg_torch_api albentrs/fdpg_torch_api:0.0.1
#docker push albentrs/fdpg_torch_api:0.0.1