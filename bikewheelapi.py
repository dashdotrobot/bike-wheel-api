from flask import Flask


app = Flask(__name__)


# --------------------------------- ROUTES --------------------------------- #
# Define application endpointsn                                              #
# -------------------------------------------------------------------------- #
@app.route('/')
def hello():
	return 'Hello World'

@app.route('/deform')
def get_deformation():
	'Return the deformation of a wheel under a set of loads'
	pass

@app.route('/tensions')
def get_tensions():
	'Return the spoke tensions of a wheel under a set of loads'
	pass
