# Use an official Python runtime as a parent image
FROM python:3.9-slim

# Set the working directory in the container
WORKDIR /app

# Clone the repository and checkout the test branch
RUN apt-get update && apt-get install -y git && \
    git clone --branch test https://github.com/tavoli-rgb/kistenverwaltung.git . && \
    apt-get remove -y git && apt-get autoremove -y && rm -rf /var/lib/apt/lists/*

# Install the necessary Python packages
RUN pip install --no-cache-dir flask mysql-connector-python

# Make port 5000 available to the world outside this container
EXPOSE 5000

# Define environment variable
ENV NAME World

# Run app.py when the container launches
CMD ["python", "app.py"]