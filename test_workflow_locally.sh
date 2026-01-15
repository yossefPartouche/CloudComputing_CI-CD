#!/bin/bash

echo "======================================"
echo "Local Workflow Test Script"
echo "======================================"

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Function to check if command succeeded
check_success() {
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓ $1${NC}"
    else
        echo -e "${RED}✗ $1${NC}"
        exit 1
    fi
}

# Clean up previous runs
echo "Cleaning up previous test runs..."
docker compose down -v
rm -f log.txt response.txt *.tar assn4_test_results.txt

# ====== JOB 1: BUILD ======
echo ""
echo "======================================"
echo "JOB 1: BUILD"
echo "======================================"

date -Iminutes > log.txt
echo "Yossi Partouche, Simon Halfon" >> log.txt

echo "Building pet-store image..."
if docker build -t pet-store:ci ./pet_store; then
    echo "image pet-store successfully built" >> log.txt
    check_success "pet-store build"
else
    echo "image pet-store not able to be built" >> log.txt
    check_success "pet-store build FAILED"
fi

echo "Building pet-order image..."
if docker build -t pet-order:ci ./pet_order; then
    echo "image pet-order successfully built" >> log.txt
    check_success "pet-order build"
else
    echo "image pet-order not able to be built" >> log.txt
    check_success "pet-order build FAILED"
fi

echo "Exporting images..."
docker save pet-store:ci -o pet-store.tar
docker save pet-order:ci -o pet-order.tar
check_success "Image export"

# ====== JOB 2: TEST ======
echo ""
echo "======================================"
echo "JOB 2: TEST"
echo "======================================"

echo "Starting containers..."
docker compose up -d --no-build
sleep 15
check_success "Container startup"

echo "Checking container status..."
docker ps --format "{{.Names}}" | grep -qx "pet-store1" && echo "Container pet-store #1 up and running" >> log.txt || echo "Container pet-store #1 failed to run" >> log.txt
docker ps --format "{{.Names}}" | grep -qx "pet-store2" && echo "Container pet-store #2 up and running" >> log.txt || echo "Container pet-store #2 failed to run" >> log.txt
docker ps --format "{{.Names}}" | grep -qx "pet-order"  && echo "Container pet-order up and running"   >> log.txt || echo "Container pet-order failed to run"   >> log.txt

echo "Running pytest..."
if pytest -v tests/assn4_tests.py > assn4_test_results.txt 2>&1; then
    echo "All pytests succeeded" >> log.txt
    check_success "Pytest execution"
else
    echo "pytests failed" >> log.txt
    echo -e "${RED}✗ Pytest execution FAILED${NC}"
    echo "Test results:"
    cat assn4_test_results.txt
fi

# ====== JOB 3: QUERY ======
echo ""
echo "======================================"
echo "JOB 3: QUERY"
echo "======================================"

echo "Seeding data..."
python seed_data.py
check_success "Data seeding"

echo "Processing queries..."
python process_queries.py
check_success "Query processing"

# ====== VERIFY OUTPUTS ======
echo ""
echo "======================================"
echo "VERIFYING OUTPUTS"
echo "======================================"

echo ""
echo "--- log.txt ---"
cat log.txt

echo ""
echo "--- assn4_test_results.txt ---"
cat assn4_test_results.txt

echo ""
echo "--- response.txt ---"
cat response.txt

# Cleanup
echo ""
echo "Cleaning up..."
docker compose down

echo ""
echo "======================================"
echo -e "${GREEN}✓ ALL TESTS COMPLETED${NC}"
echo "======================================"