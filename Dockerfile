# Use an official Python runtime as a parent image
FROM python:3.12-slim

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file into the container at /app
COPY requirements.txt .

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application's code into the container at /app
COPY . .

# The default command to run when the container starts.
# It expects the scenario path to be passed as an argument.
# For example: docker run <image_name> mission/scenarios/yinchuojiliao
ENTRYPOINT ["python", "run_scenario.py"]
