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

## Development Environment

### Python Requirements
- **Python 3.13** (required, no other versions supported)
- **UV** package manager for dependency management

### Development Tools
The project includes the following development tools:
- **Pre-commit hooks** for code quality and formatting
- **MyPy** for static type checking

### Environment Setup
The project uses environment-specific configuration files located in `.envs/`:
- `.envs/.fastapi` - FastAPI application configuration
- `.envs/.postgres` - Database configuration
- `.envs/.localstack` - LocalStack (AWS emulation) configuration

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
```

## Usage

To run the application, use the following command:

```bash
make up
```

## Testing

To test the application, use the following command:

```bash
make test
```

It will run the tests, compute the coverage and export coverage reports in the console and in html and xml format.

## Development Commands

The following make commands are available for development and interaction with the service. **Note**: The Makefile automatically detects whether you're running in a dev container or host environment and adjusts commands accordingly.

### Container Management
* `make up`: Run the application containers
* `make build`: Build docker compose images
* `make down`: Stop docker compose containers
* `make down-volumes`: Stop containers and clean up volumes
* `make restart`: Restart containers and show logs
* `make full-restart`: Restart with volume cleanup and rebuild images
* `make logs`: Follow application logs

### Development Tools
* `make bash`: Open bash inside the fastapi container (or shell if in dev container)
* `make shell`: Open Python shell with enhanced experience and imports
* `make dbshell`: Open PSQL shell
* `make localstack`: Open bash inside the localstack container

### Dependencies & Package Management
* `make lock`: Update dependencies using uv
* `make uv args="<command>"`: Execute uv commands in the container

### Database Operations
* `make make-migrations`: Create database migrations
* `make migrate`: Apply database migrations

### Testing & Quality
* `make test`: Run tests with coverage reports
* `make install-pre-commit`: Install pre-commit hooks
* `make pre-commit args="<args>"`: Run pre-commit checks

### CLI & Commands
* `make command command="<command>"`: Execute CLI commands (e.g., `make command command="users create-admin --help"`)

### Presentation & Documentation
* `make create-directories`: Create necessary directories for diagrams
* `make generate-diagrams`: Generate diagrams from Mermaid source files
* `make pptx`: Generate PowerPoint presentation from markdown
* `make clean`: Clean generated presentation files

### Help
* `make help`: Display help for all available make commands

## Built With

* [FastAPI](https://fastapi.tiangolo.com/) - The web framework used

## Versioning

We use [SemVer](http://semver.org/) for versioning. For the versions available, see the [releases on this repository](https://github.com/anmarkoulis/event-sourcing/releases).
A new version is automatically released if new code is merged in the main branch.
