SHELL := /bin/bash
IMAGE_NAME := letrus
TAG := latest
COMPOSE := docker compose

.PHONY: build push up down restart logs ps sh api ui test clean prune

build:
	@docker build -t $(IMAGE_NAME):$(TAG) .

up: build
	@$(COMPOSE) up -d

api:
	@APP_MODE=api docker run --rm -p 8000:8000 $(IMAGE_NAME):$(TAG)

ui:
	@APP_MODE=ui docker run --rm -p 8501:8501 $(IMAGE_NAME):$(TAG)

logs:
	@$(COMPOSE) logs -f --tail=200

ps:
	@$(COMPOSE) ps

restart:
	@$(COMPOSE) restart

down:
	@$(COMPOSE) down

sh:
	@docker run --rm -it --entrypoint /bin/bash $(IMAGE_NAME):$(TAG)

test:
	@docker run --rm $(IMAGE_NAME):$(TAG) pytest -q

clean:
	@docker image rm $(IMAGE_NAME):$(TAG) || true

prune:
	@docker system prune -f

help:
	@echo "Targets:"; \
	echo "  build     - Build image"; \
	echo "  up        - docker compose up (api+ui)"; \
	echo "  down      - docker compose down"; \
	echo "  api       - Run only API container"; \
	echo "  ui        - Run only Streamlit UI"; \
	echo "  logs      - Tail compose logs"; \
	echo "  ps        - Show compose services"; \
	echo "  test      - Run pytest inside image"; \
	echo "  sh        - Open bash in image"; \
	echo "  clean     - Remove built image"; \
	echo "  prune     - Docker system prune";
