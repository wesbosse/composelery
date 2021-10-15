"""
    decompose.api
    ~~~~~~~~~~~~~
    flask api facilitating the queueing of celery tasks that manage
    docker containers used for vulnerability scanning

"""
import string, os, sys
from random import choice
from dotenv import load_dotenv

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_celery import make_celery

load_dotenv()
PSQL_URI = f'{os.environ.get("PSQL_USER")}:{os.environ.get("PSQL_PASSWORD")}@{os.environ.get("PSQL_LOCATION")}'

#
#       APP CONFIG
#
app = Flask(__name__)

# location of our message broker. for us this is rabbitMQ
app.config['CELERY_BROKER_URL'] = f'amqp://{os.environ.get("AMQP_LOCATION")}'

# database for message logging, configured in init.sql and filled by rabbitMQ
app.config['CELERY_BACKEND'] = f'db+postgresql+psycopg2://{PSQL_URI}/{os.environ.get("CELERY_DB")}'

# location of our results database, configured in init.sql and filled by this API
app.config['SQLALCHEMY_DATABASE_URI'] = f'postgresql+psycopg2://{PSQL_URI}/{os.environ.get("RESULTS_DB")}'

# added this config to shut the warnings up
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True

# use custom celery wrapper and built-in sqlalchemy wrapper to bind instances
celery = make_celery(app)
db = SQLAlchemy(app)

#
#       DB CONFIG
#
class SmokeTest(db.Model):
    """smoke_test table
    -------------------
    id: sequential integer primary key
    data: random text string
    """
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
    return "Server is up, task fired"

#
#       CELERY TASKS            
#
@celery.task(name='main.insert')
def insert(int_input=1):
    """Simple Insertion: smoke test
    -------------------------------
    - generates random text string
    - formats using sqlalchemy model
    - inserts into results table
    """
    # print('attempting to generate data and commit to DB', file=sys.stderr)
    data = ''.join(choice(string.printable) for j in range(10))
    result = SmokeTest(data=data)
    db.session.add(result)
    db.session.commit()
    return f'Finished with insertion of {int_input} rows of random data'

@celery.task(name='main.standup')
def stand_up(container_name):
    """Container Creation: start container_name
    -------------------------------------------
    - starts a docker container based on existing image
    - container_name must match a valid directory in the root folder
    - leverages docker API, could be replaced with shell scripts?
    """
    return False

if __name__ == '__main__':
    app.run(debug=True)