APPLICATION_NAME = fluffie_app
DOCKER_COMPOSE = docker-compose
DOCKER_COMPOSE_EXEC = $(DOCKER_COMPOSE) exec fluffie_app

.PHONY: run
run:
	@$(DOCKER_COMPOSE) up --force-recreate --build --remove-orphans
