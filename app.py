from flask import Flask, request
from flask_cors import CORS, cross_origin
from google.oauth2 import id_token
from google.auth.transport.requests import Request
import yaml



app = Flask(__name__)

CORS(app)

creds = yaml.safe_load(open('credentials.yaml'))

@app.route('/googlelogin', methods=['POST'])
def login():
    login_data = request.json
    try:
        idinfo = id_token.verify_oauth2_token(login_data['credential'], Request(), creds['CLIENT_ID'])
        if idinfo['iss'] not in ['accounts.google.com', 'https://accounts.google.com']:
            raise ValueError('Wrong issuer.')
        # ID token is valid. Get the user's Google Account ID from the decoded token.
        userid = idinfo['sub']
        name = idinfo['name']
        email = idinfo['email']
        picture = idinfo['picture']

        print(userid, name, email, picture)
    except ValueError:
        # Invalid token
        pass

    return 'success'

if __name__ == '__main__':
    app.run()