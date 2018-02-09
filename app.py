import os
import random
import time
import json
from flask import Flask, request, render_template, session, flash, redirect, \
        url_for, jsonify, Response
from flask.ext.mail import Mail, Message
from celery import Celery


app = Flask(__name__)
app.config['SECRET_KEY'] = 'top-secret!'

# Flask-Mail configuration
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD')
app.config['SENDER'] = os.environ.get('SENDER')

# Celery configuration
app.config['CELERY_BROKER_URL'] = 'redis://localhost:6379/0'
app.config['CELERY_RESULT_BACKEND'] = 'redis://localhost:6379/0'


# Initialize extensions
mail = Mail(app)

# Initialize Celery
celery = Celery(app.name, broker=app.config['CELERY_BROKER_URL'])
celery.conf.update(app.config)


@celery.task
def send_async_email(msg):
	"""Background task to send an email with Flask-Mail."""
	with app.app_context():
		mail.send(msg)


@app.route('/', methods=['POST'])
def index():
	content = request.get_json()
	name_p = content.get('name')
	email_p = content.get('email')
	number_p = content.get('number')
	order_details_p = content.get('details')
	if email_p == None:
		data = {
		"Data": "Bad Request"
		}
		js = json.dumps(data)
		resp = Response(js, status=400, mimetype='application/json')
		return resp

	# send the email
	msg = Message('Hello from Flask',
	sender = app.config['SENDER'],
	recipients=[email_p])
	msg.body = 'Invoice for customer ' + name_p + 'contains ' + order_details_p 
	if random.choice([True, False]) == True:
		# send right away
		send_async_email.delay(msg)
		flash('Sending email to {0}'.format(email_p))
	else:
		# send in one minute
		send_async_email.apply_async(args=[msg], countdown=60)
		flash('An email will be sent to {0} in one minute'.format(email_p))
	data = {
		"Data": "Order Placed"
	}
	js = json.dumps(data)

	resp = Response(js, status=200, mimetype='application/json')
	return resp



if __name__ == '__main__':
	app.run(debug=True)
