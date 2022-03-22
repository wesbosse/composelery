# Composelery - R&D

The goal of this project was to provide a proof of concept demo for a flask service that could start and stop docker containers for use in security testing. 

## Table of Contents

- [Installation](#installation)
- [Usage](#usage)
- [Issues/Shortcuts](#issues)

## Installation

Fill out the `.env_template` accordingly before saving as `.env`


Start the project with 
```sh
docker-compose up
```

## Usage

TODO: Add postman collection

Available routes:
- /
- /list_containers
- /list_images
- /start/<container_name>
- /stop/<container_name>
- /start_all_containers
- /stop_all_containers

## Issues

Currently the repo has a few glaring issues that were left alone for time's sake.
- Celery worker being run as root
- No meaningful error handling for fragile kill_and_clean process
- Several hard-coded names/strings for things that could be done dynamically i.e. container network
- inconsistent code: I should be linting
- no tests....