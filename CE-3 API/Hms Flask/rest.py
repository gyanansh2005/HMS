from flask import Flask, request
from flask_restful import Resource, Api

app = Flask(__name__)
api = Api(app)

class HelloWorld(Resource):
    def get(self):
        return {'message': 'Hello, World!'}

    def post(self):
        data = request.get_json()
        return {'you_sent': data}, 201

api.add_resource(HelloWorld, '/')

if __name__ == '__main__':
    app.run(debug=True)
