"""
    decompose.api
    ~~~~~~~~~~~~~
    flask api facilitating the queueing of celery tasks that manage
    docker containers used for vulnerability scanning

"""
import string
import os
import sys
import docker

from random import choice
from dotenv import load_dotenv
from dataclasses import dataclass

from flask import Flask, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_celery import make_celery


load_dotenv()
PSQL_URI = f'{os.environ.get("PSQL_USER")}:{os.environ.get("PSQL_PASSWORD")}@{os.environ.get("PSQL_LOCATION")}'
docker_client = docker.from_env()

#
#       APP CONFIG
#
app = Flask(__name__)
app.config['CELERY_BROKER_URL'] = f'amqp://{os.environ.get("AMQP_LOCATION")}'
app.config['CELERY_BACKEND'] = f'db+postgresql+psycopg2://{PSQL_URI}/{os.environ.get("CELERY_DB")}'
app.config['SQLALCHEMY_DATABASE_URI'] = f'postgresql+psycopg2://{PSQL_URI}/{os.environ.get("RESULTS_DB")}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True

# use custom celery wrapper and built-in sqlalchemy wrapper to bind instances
celery = make_celery(app)
db = SQLAlchemy(app)

#
#       DB CONFIG
#
@dataclass
class SmokeTest(db.Model):
    """smoke_test table
    -------------------
    id: sequential integer primary key
    data: random text string
    """

    id: int
    data: str

    id = db.Column('id', db.Integer, primary_key=True)
    data = db.Column('data', db.String(50))

#
#       FLASK ROUTES
#
@app.route('/')
def root():
    """Root: smoke test
    -------------------
    - Confirms that the server is up and responding
    - Fires off celery task
    - Task results in DB insertion (results table)
    """
    # print('root is alive: logging up', file=sys.stderr)
    insert.delay(1)
    return jsonify(SmokeTest.query.limit(10).all())

@app.route('/start/<container_name>')
def start(container_name):
    """Start Container: container_name
    --------------------
    - cleans up any existing containers with the same name
    - then runs the container using dockerfile in test_images
    """
    if container_name in list_containers()['custom_containers_running']:
        kill_and_clean(container_name)
    
    build_and_run.delay(container_name)
    return f'task queued: build_and_run({container_name})'


@app.route('/stop/<container_name>')
def stop(container_name):
    """Stop Container: container_name
    --------------------
    - tears down container with given name
    - removes image as well, uses celery task to accomplish both
    """
    kill_and_clean.delay(container_name)
    return f'task queued: kill_and_clean({container_name})'


@app.route('/list_images')
def list_images():
    """List all images that are currently visible to the docker client
    """
    images = docker_client.images.list()
    return jsonify({
        '__count': len(images),
        'images': [image.attrs for image in images]
    })

@app.route('/list_containers')
def list_containers():
    """List all containers that are marked with our custom label
    """
    # add the container's name to the list if it has the custom label
    filtered_containers = [container.attrs for container in docker_client.containers.list() if 'custom.created_by_api' in container.attrs['Config']['Labels']]
    
    return jsonify({
        '__count': len(filtered_containers),
        'containers': filtered_containers
    })


@app.route('/start_all_containers')
def start_all():
    """Iterate through our directory of images and start a container for each one
    """
    image_names = []

    for _, dirs, __ in os.walk('/test_images'):
        for image_name in dirs:
            image_names.append(image_name)
            build_and_run.delay(image_name)
    
    return jsonify({
        '__count': len(image_names),
        'images_used': image_names
    })
    


@app.route('/stop_all_containers')
def stop_all():
    """Stops all running containers, cleans up the images as well
    """
    filtered_containers = [container.attrs for container in docker_client.containers.list() if 'custom.created_by_api' in container.attrs['Config']['Labels']]
    
    for container in filtered_containers:
        kill_and_clean(container['Name'])

    image_names = []

    for _, dirs, __ in os.walk('/test_images'):
        for image_name in dirs:
            try:
                docker_client.images.remove(image_name)
            except: 
                pass
    
    return jsonify({
        '__count': len(filtered_containers),
        'containers': filtered_containers
    })

    
#
#       CELERY TASKS            
#
@celery.task(name='main.insert')
def insert(int_input=1):
    """Simple Insertion: smoke test
    -------------------------------
    - generates random text strings
    - shoves them into db for stress testing and benchmarking
    """
    # print('attempting to generate data and commit to DB', file=sys.stderr)
    data = ''.join(choice(string.printable) for j in range(10))
    result = SmokeTest(data=data)
    db.session.add(result)
    db.session.commit()
    return f'Finished with insertion of {int_input} rows of random data'

@celery.task(name='main.build_and_run')
def build_and_run(container_name):
    """Container Creation: start container_name (str, must be valid container name)
    """
    image = docker_client.images.build(
        rm=True,
        tag=container_name,
        path=f'/test_images/{container_name}'
    )[0].attrs['Id']

    container = docker_client.containers.run(
        image,
        tty=True,
        detach=True,
        name=container_name,
        network_mode='container:composelery_api_1',
        labels={
            'custom.container_name': container_name,
            'custom.created_by_api': 'true'
        }
    ).attrs['Id']

    return container

@celery.task(name='main.kill_and_clean')
def kill_and_clean(container_name):
    """Container Creation: tear down container_name (str, must be valid container name)
    """
    container = docker_client.containers.get(container_name)
    image_id = container.attrs['Image']

    try:
        docker_client.images.remove(image_id, force = True)
    except:
        pass

    container.remove(force=True)
    
    return container.attrs


if __name__ == '__main__':
    app.run(debug=True)