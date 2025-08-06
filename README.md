# Event Sourcing

This is an example Event Sourcing project

## Documentation

This project contains comprehensive documentation organized in two main areas:

### 📊 [Presentation Documentation](docs/presentation/)
- **Presentation slides**: `docs/presentation/presentation.md` - Main presentation with speaker notes
- **Generated files**: PowerPoint presentations and diagrams
- **Diagrams**: Mermaid source files and generated images

### 📚 [Code Documentation](docs/code/)
- **[Event Sourcing Guide](docs/code/event-sourcing.md)** - Complete API documentation, architecture overview, and business rules
- **[Infrastructure Guide](docs/code/infrastructure.md)** - Database models, infrastructure components, and technical implementation details

## Prerequisites

In order to be able to run Event Sourcing locally the following are required:

* `docker`. Use instructions from [here](https://docs.docker.com/get-docker/) and [here](https://docs.docker.com/engine/install/linux-postinstall/)
* `docker compose`. Use instructions from [here](https://docs.docker.com/compose/install/)

## Installation

1. Clone the repository:

```bash
git clone git@github.com:anmarkoulis/event-sourcing.git
```

2. Navigate to the project directory:

```bash
cd event-sourcing
```

3. Build the Docker image:

```bash
make build
````

## Usage

To run the application, use the following command:

```bash
make up
````

## Testing

To test the application, use the following command:

Run
```bash
make test
```

It will run the tests, compute the coverage and export coverage reports in the console and in html and xml format.

## Development commands

The following make commands are available for development and interaction with the service:

* `make down`:  Stops the running containers
* `make down-volumes`: Stops the running containers and deletes the volumes.
* `make restart`:  Stops, restarts the containers and shows the logs of the application.
* `make full-restart`: Stops the running containers and removes their volumes, builds and restarts the containers and shows the logs of the application.
* `make logs`:  Shows the logs of the application.
* `make install-pre-commit`: Install pre-commit via docker.
* `make pre-commit args="<args>"`: Runs precommits based on the provided args.
* `make make-migrations`: Populates the migrations.
* `make migrate`: Executes the migrations.
* `make rollback args="<args>"`. Rollback to the specified migration
* `make bash`: Open bash inside the fastapi container.
* `make dbshell`: Opens a PSQL shell.
* `make uv args="<command>"`: Execute commands via uv.
* `make lock`: Lock dependencies using uv.
* `make command command=<command>"`. Execute the given command based on its path.
* `make swaggerhub`. Populate the swaggerhub definition.
* `make localstack`. Open bash inside the localstack container.

## Built With

* [FastAPI](https://fastapi.tiangolo.com/) - The web framework used

## Versioning

We use [SemVer](http://semver.org/) for versioning. For the versions available, see the [releases on this repository](https://github.com/anmarkoulis/event-sourcing/releases).
A new version is automatically released if new code is merged in the main branch.
