import jwt
from flask import jsonify

def encode_token(app, response, user_id):
    token = jwt.encode({
        'user_id': user_id,
    }, app.config['SECRET_KEY'])

    return jsonify({"response": response, "token": token}), 200

def decode_token(app, user_id, token):
    try:
        data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
        if data["user_id"] == user_id:
            return True
    except jwt.ExpiredSignatureError:
        print("Token expired")
        return False
    except jwt.InvalidTokenError:
        print("Invalid token")
        return False

    return False
