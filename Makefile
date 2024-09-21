# Define variables
VENV_DIR = venv
PYTHON = $(VENV_DIR)/bin/python
PIP = $(VENV_DIR)/bin/pip
PYTEST = $(VENV_DIR)/bin/pytest
uvicorn = $(VENV_DIR)/bin/uvicorn
COMPOSE=docker-compose

# # Create virtual environment
# $(VENV_DIR)/bin/activate: requirements.txt
# 	python3 -m venv $(VENV_DIR)
# 	$(PIP) install -r requirements.txt
# 	touch $(VENV_DIR)/bin/activate

# Install dependencies
# install: $(VENV_DIR)/bin/activate

setup:
	$(PIP) install -r requirements.txt

# Run tests
test: 
	$(PYTEST)

# freeze requirements
freeze:
	$(PIP) freeze > requirements.txt

# Start server
run: 
	$(uvicorn) api.main:app --reload

# Clean up
clean:
	rm -rf $(VENV_DIR)
	find . -type f -name '*.pyc' -delete
	find . -type d -name '__pycache__' -delete

.PHONY: install test run clean


# Rodar o Docker Compose em modo daemon
up:
	$(COMPOSE) up -d

# Parar e remover os containers
down:
	$(COMPOSE) down

# Verificar o status dos containers
ps:
	$(COMPOSE) ps

# Visualizar os logs dos containers
logs:
	$(COMPOSE) logs -f

# Rebuild dos containers
rebuild:
	$(COMPOSE) up -d --build

# Acesso ao shell dentro do container backend
shell:
	$(COMPOSE) exec backend /bin/bash