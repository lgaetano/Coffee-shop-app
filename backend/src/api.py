import os
from flask import Flask, request, jsonify, abort
from sqlalchemy import exc
import json
from flask_cors import CORS

from .database.models import db_drop_and_create_all, setup_db, Drink
from .auth.auth import AuthError, requires_auth

app = Flask(__name__)
setup_db(app)
CORS(app)

'''
@DONE uncomment the following line to initialize the datbase
!! NOTE THIS WILL DROP ALL RECORDS AND START YOUR DB FROM SCRATCH
!! NOTE THIS MUST BE UNCOMMENTED ON FIRST RUN
!! Running this funciton will add one
'''
# db_drop_and_create_all()

# ROUTES
'''
@DONE: implement GET /drinks endpoint
'''
@app.route('/drinks', methods=['GET'])
def get_drinks():
    ''' Retrieve drinks for homepage. '''
    drinks = [drink.short() for drink \
        in Drink.query.all()]

    return jsonify({
        "success": True,
        "drinks": drinks
    }), 200


'''
@DONE implement GET /drinks-detail endpoint
'''
@app.route('/drinks-detail', methods=['GET'])
@requires_auth('get:drinks-detail')
def get_drinks_detail(payload):
    ''' Retrieve drink recipes. '''

    drinks = [drink.long() for drink \
        in Drink.query.all()]

    return jsonify({
        "success": True,
        "drinks": drinks
    }), 200

'''
@DONE implement POST /drinks endpoint
'''
@app.route('/drinks', methods=['POST'])
@requires_auth('post:drinks')
def create_drink(payload):
    ''' Create a new drink. '''
    
    # Get data from body
    data = request.get_json()

    title = data.get("title", None)
    recipe = json.dumps(data["recipe"])

    # If no drink title supplied, abort
    if not title:
        abort(422)
    # If no drink recipe supplied, abort
    if not recipe:
        abort(422)

    try:
        # Create a new drink
        drink = Drink(title=title, recipe=recipe)
        # Insert new drink
        drink.insert()

    except Exception as e:
        print('ERROR: ', str(e))
        abort(400)
    
    return jsonify({
        "success": True,
        "drinks": [drink.long()]
    }), 200

'''
@DONE implement  PATCH /drinks/<id> endpoint
'''
@app.route('/drinks/<int:id>', methods=['PATCH'])
@requires_auth('patch:drinks')
def update_drinks(payload, id):
    ''' Update existing drink. '''
    
    # Get drink with requested id
    drink = Drink.query.filter(Drink.id == id).one_or_none()

    # If no drink with id, abort
    if not drink:
        abort(404)

    # Get data from frontend
    data = request.get_json()
    try:
        title = data.get("title")
        recipe = json.dumps(data["recipe"])

        # If new title provided, add to obj
        if title:
            drink.title = title
        # If new recipe provided, add to obj
        if recipe:
            # drink.recipe = recipe
            drink.recipe = recipe if type(recipe) == str else json.dumps(recipe)

        # Update drink with new information
        drink.update()
    except Exception:
        abort(400)

    return jsonify({
        "success": True,
        "drinks": [drink.long()]
    }), 200


'''
@DONE implement DELETE /drinks/<id> endpoint
'''
@app.route('/drinks/<int:id>', methods=['DELETE'])
@requires_auth('delete:drinks')
def delete_drink(payload, id):
    ''' Delete existing drink. '''

    # Get drink with requested id
    drink = Drink.query.filter(Drink.id == id).one_or_none()
    
    # # If no drink with id, abort
    if not drink:
        abort(404)
    try:
        # Delete drink
        drink.delete()
    except Exception as e:
        abort(400)

    return jsonify({
        "success": True,
        "delete": id 
    }), 200

# Error Handling

@app.errorhandler(400)
def bad_request(error):
    return jsonify({
        "success": False,
        "error": 400,
        "message": "bad request"
    }), 400

@app.errorhandler(403)
def forbidden(error):
    return jsonify({
        "success": False,
        "error": 403,
        "message": "forbidden"
    }), 403

@app.errorhandler(404)
def not_found(error):
    return jsonify({
        "success": False,
        "error": 404,
        "message": "not found"
    }), 404

@app.errorhandler(422)
def unprocessable(error):
    return jsonify({
        "success": False,
        "error": 422,
        "message": "unprocessable"
    }), 422

@app.errorhandler(500)
def internal_server_error(error):
    return jsonify({
        "success": False,
        "error": 500,
        "message": "internal server error"
    }),  500

@app.errorhandler(AuthError)
def authentication_failed(error):
    return jsonify({
        "success": False,
        "error": error.status_code,
        "message": error.error['code']
    }), error.status_code