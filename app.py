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

@app.route('/share/<filename>')    
def share(filename):
    image_url = f'https://mighty-macaque-30f16fdc84f3.herokuapp.com/images/{filename}'
    instagram_url = f'instagram://story-camera?AssetPath={image_url}'

    redirect_page = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta http-equiv="refresh" content="0; url={instagram_url}">
        <title>Redirecting...</title>
    </head>
    <body>
        <p>If you are not redirected automatically, follow this <a href="{instagram_url}">link to share on Instagram</a>.</p>
    </body>
    </html>
    """
    return render_template_string(redirect_page)

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)