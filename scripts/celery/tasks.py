from celery import Celery

#app = Celery('tasks', broker = 'redis://localhost:6379/0', backend='redis://localhost:6379')
app = Celery('tasks')
app.config_from_object('celeryconfig')

import scripts.celery.pipeline_tasks
import scripts.celery.results_parser_tasks
import scripts.celery.select_ids_tasks

@app.task
def add(x, y):
    return x + y

@app.task
def divide(x, y):
    return x / y

@app.task
def multiply(x, y):
    return x*y

@app.task
def subtract(x, y):
    return x-y

@app.task
def power(x, y):
    return [x ** y]

@app.task
def mean(x):
    return sum(x)/len(x)

@app.task
def diff_vect(y, x):
    diffs = []
    for value in x:
        diffs.append(value-y)
    return diffs

@app.task
def sq_vect(x):
    sqs = []
    for value in x:
        sqs.append(value ** 2)
    return sqs
