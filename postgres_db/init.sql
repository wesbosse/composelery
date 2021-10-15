DROP DATABASE IF EXISTS celery;
DROP DATABASE IF EXISTS results;

CREATE DATABASE celery;
CREATE DATABASE results;
\c results;
CREATE TABLE smoke_test(
    id serial PRIMARY KEY,
    data VARCHAR(50)
);