#!/bin/bash

echo "====================================================="
echo " Starting Web War Cyber Game Development Environment "
echo "====================================================="
echo "Building and launching containers via Docker Compose..."
echo " - Frontend will be available at: http://localhost:5173"
echo " - Backend API will be available at: http://localhost:8000"
echo " - Database running on port: 5432"
echo ""

# Run docker-compose using the dev file
docker-compose -f docker-compose.dev.yml up --build
