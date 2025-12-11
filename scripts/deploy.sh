#!/bin/bash

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

ENVIRONMENT=$1
TARGET=$2

if [ -z "$ENVIRONMENT" ] || [ -z "$TARGET" ]; then
    echo -e "${RED}Usage: ./deploy.sh <environment> <target>${NC}"
    echo "Example: ./deploy.sh staging staging"
    exit 1
fi

echo -e "${GREEN}🚀 Starting deployment to $ENVIRONMENT environment...${NC}"

# 1. Pre-deployment checks
echo -e "${YELLOW}📋 Running pre-deployment checks...${NC}"
cd dbt

# Install dependencies
echo "Installing DBT dependencies..."
dbt deps --target $TARGET --profiles-dir .

# Compile models
echo "Compiling DBT models..."
dbt compile --target $TARGET --profiles-dir .

if [ $? -ne 0 ]; then
    echo -e "${RED}❌ Compilation failed${NC}"
    exit 1
fi

# 2. Run tests on current state
echo -e "${YELLOW}🧪 Running tests...${NC}"
dbt test --target $TARGET --profiles-dir .

if [ $? -ne 0 ]; then
    echo -e "${RED}❌ Tests failed${NC}"
    exit 1
fi

# 3. Backup current state
echo -e "${YELLOW}💾 Creating backup...${NC}"
timestamp=$(date +%Y%m%d_%H%M%S)
backup_dir="../backups/${ENVIRONMENT}_${timestamp}"
mkdir -p $backup_dir
cp -r target/ $backup_dir/

echo "Backup created at: $backup_dir"
# Export backup dir for GitHub Actions
if [ -n "$GITHUB_ENV" ]; then
    echo "BACKUP_DIR=$backup_dir" >> $GITHUB_ENV
fi

# 4. Deploy models
echo -e "${YELLOW}🔨 Deploying models...${NC}"
dbt run --target $TARGET --profiles-dir .

if [ $? -ne 0 ]; then
    echo -e "${RED}❌ Deployment failed${NC}"
    exit 1
fi

# 5. Run post-deployment tests
echo -e "${YELLOW}✅ Running post-deployment tests...${NC}"
dbt test --target $TARGET --profiles-dir .

if [ $? -ne 0 ]; then
    echo -e "${RED}❌ Post-deployment tests failed${NC}"
    exit 1
fi

# 6. Generate documentation
echo -e "${YELLOW}📚 Generating documentation...${NC}"
dbt docs generate --target $TARGET --profiles-dir .

# 7. Success message
echo -e "${GREEN}✨ Deployment to $ENVIRONMENT completed successfully!${NC}"
echo ""
echo "Summary:"
echo "  Environment: $ENVIRONMENT"
echo "  Target: $TARGET"
echo "  Time: $(date)"
echo "  Backup: $backup_dir"
