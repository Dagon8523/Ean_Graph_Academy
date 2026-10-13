You are working on the GenChAIn project (Generative Supply Chain using AI) for Ecopetrol S.A.
Your task is to implement Sprint 0: Azure Infrastructure Base.

Read CLAUDE.md before doing anything else. Follow all working principles and editing rules defined there.
Create docs/sprint_0/ now. All documentation you produce during this sprint goes there.

---

## CONTEXT

The goal of Sprint 0 is to provision all Azure resources needed as the foundation for GenChAIn.
Everything must be Infrastructure as Code (Bicep), parameterized for dev/staging/prod environments,
and follow zero-secrets-in-code discipline (Managed Identity + Key Vault for everything).

The repository was just initialized with git. Python virtual environment has been created at .venv/
using Python 3.12. The venv is already active.

I will provide you with:
- Azure subscription ID
- Tenant ID
- Location preference
- Naming prefix convention
- Any existing resource constraints or policies from Ecopetrol's Azure environment

Ask me for these values before writing any Bicep file that requires them.

---

## DELIVERABLES

Implement the following in order. Complete each item fully before moving to the next.
After each item, report: files created/modified, validation performed, risks or follow-ups.

### 1. Repository foundation files

#### 1a. Folder structure
Verify the folder structure defined in CLAUDE.md exists. Create any missing folders.
For every empty folder, add a .gitkeep file so git tracks it.

#### 1b. .gitignore
Create .gitignore at the repo root covering exactly these categories.
Add a clear section comment before each group:

# Python
.venv/
__pycache__/
*.py[cod]
*.pyo
*.pyd
.Python
*.egg
*.egg-info/
dist/
build/
eggs/
parts/
var/
sdist/
wheels/
pip-wheel-metadata/
.installed.cfg
*.egg-link
.pytest_cache/
.mypy_cache/
.ruff_cache/
htmlcov/
.coverage
.coverage.*
coverage.xml
*.cover
nosetests.xml
pytestdebug.log

# Virtual environments
.venv/
venv/
ENV/
env/

# Environment and secrets — never commit these
.env
.env.local
.env.*.local
*.pem
*.key
*.p12
*.pfx

# Node / React (apps/web/)
node_modules/
apps/web/build/
apps/web/.next/
apps/web/dist/
npm-debug.log*
yarn-debug.log*
yarn-error.log*
.pnp.*

# Docker
.dockerignore

# Data — raw and generated data never goes to git
data/raw/
data/interim/
data/processed/
data/external/

# Artifacts and generated outputs
artifacts/
reports/

# Notebooks — strip outputs before committing, but ignore checkpoint folders
notebooks/.ipynb_checkpoints/

# IDE
.vscode/settings.json
.idea/
*.swp
*.swo
*~

# OS
.DS_Store
Thumbs.db
desktop.ini

# Azure / Terraform state (in case it appears)
*.tfstate
*.tfstate.backup
.terraform/

# Logs
*.log
logs/

#### 1c. .env.example
Create .env.example at the repo root.
This is the reference template for all developers. It must contain every variable
the application needs, with placeholder values and a one-line comment explaining each.
Never put real values here — this file IS committed to git.

Content:

# =============================================================================
# GenChAIn — Environment variables reference
# Copy this file to .env and fill in the real values for local development.
# Production values are managed via Azure Key Vault + Managed Identity.
# NEVER commit .env — it is in .gitignore.
# =============================================================================

# --- Application ---
APP_ENVIRONMENT=dev                         # dev | staging | prod
LOG_LEVEL=INFO                              # DEBUG | INFO | WARNING | ERROR

# --- Azure identity ---
AZURE_TENANT_ID=your-tenant-id-here
AZURE_CLIENT_ID=your-client-id-here        # Used in local dev only; MI is used in prod
AZURE_CLIENT_SECRET=your-client-secret     # Used in local dev only; never in prod

# --- Azure OpenAI ---
AZURE_OPENAI_ENDPOINT=https://<resource>.openai.azure.com/
AZURE_OPENAI_API_VERSION=2024-02-01
AZURE_OPENAI_CHAT_DEPLOYMENT=gpt-4o
AZURE_OPENAI_MINI_DEPLOYMENT=gpt-4o-mini
AZURE_OPENAI_REASONING_DEPLOYMENT=o3
AZURE_OPENAI_EMBEDDING_DEPLOYMENT=text-embedding-3-large

# --- Azure AI Search ---
AZURE_SEARCH_ENDPOINT=https://<resource>.search.windows.net
AZURE_SEARCH_INDEX_PREFIX=genchain         # Indexes: genchain-crudo, genchain-gas, etc.

# --- Azure Cosmos DB ---
COSMOS_ENDPOINT=https://<resource>.documents.azure.com:443/
COSMOS_DATABASE=genchain-db
COSMOS_CONTAINER_CONVERSATIONS=conversations

# --- Azure Cache for Redis ---
REDIS_HOSTNAME=<resource>.redis.cache.windows.net
REDIS_PORT=6380
REDIS_SSL=true

# --- Azure Key Vault ---
KEY_VAULT_URI=https://<resource>.vault.azure.net/

# --- Azure Application Insights ---
APPLICATIONINSIGHTS_CONNECTION_STRING=InstrumentationKey=...

# --- Entra ID (Auth) ---
ENTRA_TENANT_ID=your-tenant-id-here
ENTRA_CLIENT_ID=your-web-app-client-id
ENTRA_AUDIENCE=api://your-api-client-id   # The audience the backend validates in JWT tokens

# --- Semantic cache ---
SEMANTIC_CACHE_SIMILARITY_THRESHOLD=0.92   # Cosine similarity threshold (0.0 - 1.0)
SEMANTIC_CACHE_TTL_SECONDS=3600            # 1 hour

# --- Context window ---
CONTEXT_WINDOW_FULL_TURNS=10              # Number of most recent turns sent in full
CONTEXT_WINDOW_MAX_SUMMARY_TOKENS=800     # Max tokens for compressed older turns

#### 1d. pyproject.toml
Create pyproject.toml at the repo root with this exact content.
Do not add sections or dependencies beyond what is specified here:

[build-system]
requires = ["setuptools>=68", "wheel"]
build-backend = "setuptools.backends.legacy:build"

[project]
name = "genchain"
version = "0.1.0"
description = "GenChAIn — Generative Supply Chain using AI for Ecopetrol GGO"
readme = "README.md"
license = { file = "LICENSE" }
requires-python = ">=3.12"
authors = [
  { name = "Andrés Felipe Rojas Parra", email = "" },
]

[project.urls]
Repository = "https://dev.azure.com/ecopetrol/genchAIn"

[tool.ruff]
target-version = "py312"
line-length = 100
src = ["src", "apps", "tests"]

[tool.ruff.lint]
select = [
  "E",   # pycodestyle errors
  "W",   # pycodestyle warnings
  "F",   # pyflakes
  "I",   # isort
  "B",   # flake8-bugbear
  "C4",  # flake8-comprehensions
  "UP",  # pyupgrade
]
ignore = [
  "E501",  # line too long — handled by formatter
]

[tool.ruff.lint.isort]
known-first-party = ["src", "apps"]

[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py", "*_test.py"]
python_classes = ["Test*"]
python_functions = ["test_*"]
asyncio_mode = "auto"
addopts = "--strict-markers -q"

[tool.coverage.run]
source = ["src"]
omit = ["tests/*", "**/__init__.py"]

[tool.coverage.report]
fail_under = 70
show_missing = true

#### 1e. requirements.txt
Create requirements.txt with pinned major versions (allow minor/patch with ~=).
Add a comment grouping dependencies by purpose:

# Web framework
fastapi~=0.111
uvicorn[standard]~=0.29

# AI orchestration
semantic-kernel~=1.3

# Azure identity and services
azure-identity~=1.17
azure-keyvault-secrets~=4.8
azure-cosmos~=4.7
azure-search-documents~=11.6
azure-monitor-opentelemetry~=1.4

# Caching
redis~=5.0

# OpenAI client (used by Semantic Kernel)
openai~=1.30

# Auth token validation
python-jose[cryptography]~=3.3

# Configuration
pydantic-settings~=2.3
pydantic~=2.7

# Observability
opentelemetry-api~=1.25
opentelemetry-sdk~=1.25

#### 1f. requirements-dev.txt
Create requirements-dev.txt:

# Testing
pytest~=8.2
pytest-cov~=5.0
pytest-asyncio~=0.23
httpx~=0.27          # async HTTP client for FastAPI test client

# Linting and formatting
ruff~=0.4

# Notebook output stripping (pre-commit hook)
nbstripout~=0.7

# Local development utilities
python-dotenv~=1.0

#### 1g. LICENSE
Create LICENSE at the repo root.
Use the MIT license with the following customization:

MIT License

Copyright (c) 2025 Ecopetrol S.A. — Vicepresidencia de Tecnología e Innovación (VTI)
Gestión de Gas y Operaciones (GGO) — Analítica Avanzada

Authors:
  Andrés Felipe Rojas Parra — Data Scientist
  Francisco Medina — Advanced Analytics Lead
  Rohyman Ramos — GGO Lead

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

#### 1h. Sprint 0 documentation
Create docs/sprint_0/README.md with this structure:

#### 1i. Makefile
Create Makefile at the repo root.
It must work on Windows 11 PowerShell, Windows 11 Git Bash, and Ubuntu 24.04.
Use GNU Make (install via winget install GnuWin32.Make or chocolatey on Windows).

Key constraints for cross-platform compatibility:
- No bash-specific commands (no find, no rm -rf, no echo with color codes)
- Use Python -c for any file system operations in the clean target
- Use forward slashes in paths
- Use $(PYTHON) instead of python3 anywhere
- The ifeq OS detection block must cover both PowerShell and Git Bash on Windows

Content:

# =============================================================================
# GenChAIn — Makefile
# Requires: GNU Make
# Windows:  winget install GnuWin32.Make  (then add to PATH)
#           Works in PowerShell and Git Bash
# Ubuntu:   works natively
# =============================================================================

PYTHON := python

ifeq ($(OS),Windows_NT)
  VENV_BIN  := .venv/Scripts
  SEP       := \\
else
  VENV_BIN  := .venv/bin
  SEP       := /
endif

PIP     := $(VENV_BIN)/pip
PYTEST  := $(VENV_BIN)/pytest
RUFF    := $(VENV_BIN)/ruff
UVICORN := $(VENV_BIN)/uvicorn

.PHONY: help venv install install-dev lint lint-fix test test-cov \
        test-integration test-e2e run-api docker-build docker-up \
        docker-down docker-logs clean freeze

help:               ## Show this help message
	$(PYTHON) -c "import re; [print('  {:<20}{}'.format(m[0], m[1])) for line in open('Makefile') for m in re.findall(r'^([a-zA-Z_-]+):.*?## (.+)', line)]"

venv:               ## Create virtual environment
	$(PYTHON) -m venv .venv
	@echo "Activate with:"
	@echo "  PowerShell:  .venv\Scripts\Activate.ps1"
	@echo "  Git Bash:    source .venv/Scripts/activate"
	@echo "  Ubuntu:      source .venv/bin/activate"

install:            ## Install runtime dependencies
	$(PYTHON) -m pip install --upgrade pip wheel setuptools
	$(PIP) install -r requirements.txt

install-dev:        ## Install runtime + dev dependencies
	$(PYTHON) -m pip install --upgrade pip wheel setuptools
	$(PIP) install -r requirements.txt -r requirements-dev.txt

lint:               ## Run ruff linter on src/, apps/, tests/
	$(RUFF) check src/ apps/ tests/

lint-fix:           ## Run ruff and auto-fix safe issues
	$(RUFF) check --fix src/ apps/ tests/

test:               ## Run unit tests
	$(PYTEST) tests/unit/ -q

test-cov:           ## Run unit tests with coverage report
	$(PYTEST) tests/unit/ --cov=src --cov-report=term-missing --cov-fail-under=70

test-integration:   ## Run integration tests (requires running services)
	$(PYTEST) tests/integration/ -q

test-e2e:           ## Run end-to-end tests
	$(PYTEST) tests/e2e/ -q

run-api:            ## Start FastAPI development server
	$(UVICORN) apps.api.src.main:app --host 0.0.0.0 --port 8000 --reload

docker-build:       ## Build all Docker images
	docker compose -f ops/docker/docker-compose.yml build

docker-up:          ## Start local stack (orchestrator + redis)
	docker compose -f ops/docker/docker-compose.yml up -d

docker-down:        ## Stop local stack
	docker compose -f ops/docker/docker-compose.yml down

docker-logs:        ## Tail logs from local stack
	docker compose -f ops/docker/docker-compose.yml logs -f

clean:              ## Remove cache and build artifacts
	$(PYTHON) -c "import shutil, pathlib; [shutil.rmtree(p, ignore_errors=True) for p in pathlib.Path('.').rglob('__pycache__')]"
	$(PYTHON) -c "import shutil, pathlib; [shutil.rmtree(p, ignore_errors=True) for p in pathlib.Path('.').rglob('.pytest_cache')]"
	$(PYTHON) -c "import shutil, pathlib; [shutil.rmtree(p, ignore_errors=True) for p in pathlib.Path('.').rglob('.ruff_cache')]"
	$(PYTHON) -c "import shutil, pathlib; [shutil.rmtree(p, ignore_errors=True) for p in pathlib.Path('.').rglob('htmlcov')]"
	$(PYTHON) -c "import pathlib; [p.unlink() for p in pathlib.Path('.').rglob('*.pyc')]"
	$(PYTHON) -c "import pathlib; [p.unlink(missing_ok=True) for p in [pathlib.Path('.coverage')]]"

freeze:             ## Export current venv dependencies to requirements.lock
	$(PIP) freeze > requirements.lock
	@echo "Saved to requirements.lock"

# Sprint 0 — Infrastructure Base

## Goal
Provision all Azure resources required as the foundation for GenChAIn using Bicep IaC.

## Deliverables
- [ ] Repository foundation files (structure, .gitignore, .env.example, pyproject.toml, LICENSE)
- [ ] Bicep module: networking (VNet, subnets, NSGs)
- [ ] Bicep module: Azure Container Registry
- [ ] Bicep module: Azure Key Vault
- [ ] Bicep module: Cosmos DB
- [ ] Bicep module: Azure Cache for Redis
- [ ] Bicep module: Log Analytics + Application Insights
- [ ] Bicep module: Managed Identity + RBAC
- [ ] Bicep module: Azure Container Apps environment
- [ ] Bicep main orchestrator + parameter files
- [ ] src/config/ foundation (Pydantic Settings)
- [ ] src/observability/ foundation (logging + OpenTelemetry)
- [ ] CI pipeline foundation (azure-pipelines-ci.yml)
- [ ] Docker foundation (Dockerfile + docker-compose.yml)

## Decisions made this sprint
<!-- Add ADRs and key decisions here as the sprint progresses -->

## Setup instructions for new developers
1. Clone the repository
2. Create and activate the virtual environment:
   python -m venv .venv
   # Windows: .venv\Scripts\activate
   # Linux/Mac: source .venv/bin/activate
3. Install dependencies:
   pip install -r requirements.txt -r requirements-dev.txt
4. Copy .env.example to .env and fill in local values
5. Run linting: ruff check src/ tests/ apps/
6. Run tests: pytest tests/unit/

---

After completing deliverable 1, run the following validations and report results:
- Confirm all folders exist with .gitkeep where needed
- Confirm ruff can be installed and runs without error on the (currently empty) src/ folder
- Confirm pytest discovers the tests/ folder correctly
- List every file created

Then stop and wait for my confirmation before starting deliverable 2 (Bicep networking module).

---

### 2. Bicep modules — networking
File: ops/bicep/modules/networking.bicep
- Resource Group (parametrized: environment, location, prefix)
- Virtual Network with three subnets: app-subnet, data-subnet, management-subnet
- NSG per subnet with minimum required rules (least-privilege)
- Parametrized: environment (dev/staging/prod), location, prefix
- Output: vnetId, subnetIds

### 3. Bicep modules — Azure Container Registry
File: ops/bicep/modules/acr.bicep
- SKU: Premium (required for private networking)
- Admin account: disabled
- Private endpoint on data-subnet
- Retention policy: 30 tags max per repository
- Managed Identity access only (AcrPull role assignment included)
- Output: acrId, acrLoginServer

### 4. Bicep modules — Azure Key Vault
File: ops/bicep/modules/keyvault.bicep
- SKU: Standard
- Soft-delete: 90 days, purge protection enabled
- RBAC enabled (no legacy Access Policies)
- Private endpoint on data-subnet
- Diagnostic settings → Log Analytics Workspace
- Output: keyVaultId, keyVaultUri

### 5. Bicep modules — Cosmos DB
File: ops/bicep/modules/cosmosdb.bicep
- API: NoSQL
- Database: genchain-db
- Container: conversations, partition key: /userId
- TTL: 31536000 seconds (365 days) as default, -1 to disable per document
- Capacity: Serverless (dev), Provisioned 400 RU/s autoscale (staging/prod)
- Backup: continuous mode
- Availability zones: enabled in prod
- Private endpoint on data-subnet
- Public access: disabled
- Output: cosmosAccountId, cosmosEndpoint

### 6. Bicep modules — Azure Cache for Redis
File: ops/bicep/modules/redis.bicep
- SKU: Standard C1 (dev), Premium P1 (prod)
- TLS 1.2 minimum, non-SSL port disabled
- Private endpoint in prod
- maxmemory-policy: allkeys-lru
- Output: redisId, redisHostName

### 7. Bicep modules — Log Analytics + Application Insights
File: ops/bicep/modules/monitoring.bicep
- Log Analytics Workspace: SKU PerGB2018
- Retention: 30 days (dev), 90 days (prod)
- Application Insights: workspace-based, linked to Log Analytics
- Base alerts:
  - Availability < 99%
  - P95 latency > 5000ms
  - Error rate > 1%
- Output: workspaceId, appInsightsConnectionString

### 8. Bicep modules — Managed Identity + RBAC
File: ops/bicep/modules/identity.bicep
- User-Assigned Managed Identity: genchain-{env}-mi
- Role assignments (least-privilege):
  - AcrPull on ACR
  - Key Vault Secrets User on Key Vault
  - Cosmos DB Built-in Data Contributor on Cosmos account
  - Redis Cache Contributor on Redis
- Output: managedIdentityId, managedIdentityClientId

### 9. Bicep modules — Azure Container Apps Environment
File: ops/bicep/modules/aca.bicep
- ACA Environment integrated to VNet (app-subnet)
- Log Analytics linked for container logs
- Dapr enabled
- Workload profile: Consumption
- Output: acaEnvironmentId, acaEnvironmentName

### 10. Bicep main orchestrator
File: ops/bicep/main.bicep
- Orchestrates all modules above in correct dependency order
- Parameters file: ops/bicep/parameters/dev.bicepparam
- Parameters file: ops/bicep/parameters/prod.bicepparam
- Outputs: all resource IDs and endpoints needed by the application

### 11. Config foundation — src/config/
File: src/config/settings.py
- Pydantic Settings class: GenChainSettings
- Reads from environment variables and .env file
- Fields: azure_openai_endpoint, azure_openai_api_version, cosmos_endpoint,
  redis_hostname, key_vault_uri, entra_tenant_id, entra_client_id,
  entra_audience, app_environment (dev/staging/prod), log_level
- All secrets resolved at runtime via azure-identity DefaultAzureCredential
- No hardcoded values

File: src/config/__init__.py
- Exports: settings (singleton instance of GenChainSettings)

### 12. Observability foundation — src/observability/
File: src/observability/logging.py
- Structured JSON logging setup using Python logging
- Includes: timestamp, level, service name, trace_id, span_id
- log_level driven by settings.log_level

File: src/observability/telemetry.py
- OpenTelemetry SDK setup
- Azure Monitor exporter (azure-monitor-opentelemetry)
- Tracer and meter providers configured from settings.app_insights_connection_string

File: src/observability/__init__.py
- Exports: setup_logging, setup_telemetry

### 13. CI pipeline foundation
File: azure-pipelines-ci.yml (root)
- Trigger: PR to develop and main
- Agent: ubuntu-latest, Python 3.12
- Stages in order:
  1. Install dependencies (pip install -r requirements-dev.txt)
  2. Lint (ruff check src/ tests/ apps/)
  3. Unit tests (pytest tests/unit/ --cov=src --cov-fail-under=70)
- Build time target: under 5 minutes
- Publish test results and coverage as pipeline artifacts

### 14. Docker foundation
File: ops/docker/orchestrator/Dockerfile
- Base: python:3.12-slim
- Non-root user
- Copies src/ and apps/api/
- Installs requirements.txt
- Exposes port 8000
- CMD: uvicorn apps.api.src.main:app --host 0.0.0.0 --port 8000

File: ops/docker/docker-compose.yml
- Services: orchestrator, redis
- Orchestrator: builds from ops/docker/orchestrator/Dockerfile, env_file: .env
- Redis: image redis:7-alpine, port 6379
- Network: genchain-net (bridge)

---

## RULES FOR THIS SPRINT

- Ask me for subscription-specific values before using them in any Bicep file.
- Never hardcode subscription IDs, tenant IDs, resource IDs, or IP ranges.
- All Bicep modules must be self-contained and reusable.
- All Bicep parameters must have @description and @allowed decorators where applicable.
- Python files must pass ruff with zero errors before you consider them done.
- Report progress after each numbered deliverable above.
- If you are unsure about an Ecopetrol-specific constraint, stop and ask before proceeding.
- Do not proceed to deliverable N+1 until I explicitly confirm deliverable N is complete.

---

## START

Begin with deliverable 1. State your plan for it in 3-4 lines, then execute.