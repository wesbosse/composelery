# Composelery - R&D

The goal of this project was to provide a proof of concept demo for a service that could start and stop docker containers for use in security testing. 

## Table of Contents

- [Installation](#installation)
- [Usage](#usage)

## Installation

Clone the repo, and then fill out the `.env_template` accordingly before saving as `.env`


Start the porject with 
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
