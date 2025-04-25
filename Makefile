# Makefile for updating and running the TrueFact Docker container

# Variables
APP_DIR := /root/truefact
IMAGE_NAME := truefact
CONTAINER_NAME := truefact
ENV_FILE := .env
PORT := 6666
NETWORK := n8n_n8n-network

.PHONY: deploy update build stop run

default: deploy

deploy: update build stop run
	@echo "✅ Deployment complete."

update:
	@echo "⏳ Updating repository..."
	cd $(APP_DIR) && git pull

build:
	@echo "📦 Building Docker image '$(IMAGE_NAME)'..."
	cd $(APP_DIR) && docker build -t $(IMAGE_NAME) .

stop:
	@echo "🛑 Stopping container '$(CONTAINER_NAME)' if running..."
	- docker stop $(CONTAINER_NAME) 2>/dev/null || true

run:
	@echo "🚀 Running container '$(CONTAINER_NAME)'..."
	cd $(APP_DIR) && \
		docker run -d --rm --env-file $(ENV_FILE) -p $(PORT):$(PORT) \
		--network $(NETWORK) --name $(CONTAINER_NAME) $(IMAGE_NAME):latest
