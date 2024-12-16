# run 'make help' in the terminal to see a list of script options

SHELL:=/bin/bash

PACKAGE=astromap
PACKAGE_DIR=astromap
VERSION:=0.1.0
REPO:=ghcr.io/the-astros
TAG:=$(REPO)/$(PACKAGE):$(VERSION)
WORKSPACE=/opt/work

.PHONY: help
help: ## Show help message
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' ${MAKEFILE_LIST} | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'

.PHONY: version
version: ## Print the package version
	@echo $(VERSION)

.PHONY: tag
tag: ## print the image tag
	@echo $(TAG)

.PHONY: run
run: ## get shell into container
	podman run --rm -it \
		--name $(PACKAGE) \
		$(TAG) \
		/bin/bash

.PHONY: install
install: image ## install local .venv
	podman run --rm \
		--volume $(PWD):$(WORKSPACE) \
		--name $(PACKAGE) \
		$(TAG) \
		/bin/bash -c "poetry install"

.PHONY: dev
dev: ## get shell into container with local disk mounted
	podman run --rm -it \
		--volume $(PWD):$(WORKSPACE) \
		--name $(PACKAGE) \
		$(TAG) \
		/bin/bash

.PHONY: shell
shell: ## get shell into running container
	podman exec -it $(PACKAGE) \
		/bin/bash

.PHONY: image
image: ## builds the container image
	podman build \
		--build-arg WORKSPACE=$(WORKSPACE) \
		--tag $(TAG) \
		.

.PHONY: clean-image
clean-image: clean ## builds the container image without cache
	podman build \
		--pull \
		--no-cache \
		--build-arg WORKSPACE=$(WORKSPACE) \
		--tag $(TAG) \
		.

.PHONY: cairo-sample
cairo-sample: ## generate sample png with cairo
	podman run --rm -it \
		--volume $(PWD):$(WORKSPACE) \
		--name $(PACKAGE) \
		$(TAG) \
		/bin/bash -c "poetry run python tests/cairo_sample.py"

.PHONY: validate
validate: image ## runs pytest to validate in podman container
	podman run --rm \
		--volume $(PWD):$(WORKSPACE) \
		--name $(PACKAGE) \
		$(TAG) \
		/bin/bash -c "poetry run isort -c . \
			&& poetry run black --check . \
			&& poetry run flake8 \
			&& poetry run mypy -p $(PACKAGE_DIR) \
			&& poetry run pytest"

.PHONY: clean
clean: ## remove venv & build artifacts
	rm -rf .venv
	rm -rf build
