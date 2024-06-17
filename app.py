from flask import Flask, jsonify, send_file, render_template_string
from pymongo import MongoClient
import os
import base64
from io import BytesIO

# Load environment variables from .env file

if os.getenv('ENV') is None:
    from dotenv import load_dotenv
    load_dotenv()

MONGODB_URI = os.getenv('MONGODB_URI')


# Connect to MongoDB
client = MongoClient(MONGODB_URI)
db = client["main"]
collection = db['app_constants']

app = Flask(__name__)

@app.route('/')
def home():
    return 'Hello, World!'

# Generate Image
@app.route('/images/<filename>')
def get_image(filename):
    # Retrieve the image document from MongoDB
    image_doc = collection.find_one({"filename": filename})
    
    if image_doc:
        # Decode the base64 image data
        image_data = image_doc['data'].split(",")[1]
        image_bytes = base64.b64decode(image_data)
        return send_file(BytesIO(image_bytes), mimetype=image_doc['filetype'])
    else:
        return jsonify({"error": "Image not found"}), 404

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)