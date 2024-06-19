import os
import base64
from pymongo import MongoClient
from bson import Binary

from dotenv import load_dotenv
load_dotenv()

MONGO_USER = os.getenv('MONGO_USER')
MONGO_PWD = os.getenv('MONGO_PWD')
MONGO_CLUSTER = os.getenv('MONGO_CLUSTER')
MONGO_APP = os.getenv('MONGO_APP')
MONGO_URI = f"mongodb+srv://{MONGO_USER}:{MONGO_PWD}@{MONGO_CLUSTER}/?retryWrites=true&w=majority&appName={MONGO_APP}"

# MongoDB Setup
client = MongoClient(MONGO_URI)
MONGO_DB = os.getenv('MONGO_DB')
db = client[MONGO_DB]
assets_col = db.assets
question_sets_col = db.question_sets

def store_image(question_id, image_path):
    with open(image_path, 'rb') as image_file:
        image_data = image_file.read()
        question_sets_col.update_one(
            {"questions.question_id": question_id},
            {"$set": {"questions.$.image": Binary(image_data)}}
        )
    print(f"Question {question_id} image updated successfully.")

def store_option_image(question_id, option_id, image_path):
    with open(image_path, 'rb') as image_file:
        image_data = image_file.read()
        binary_image = Binary(image_data)
        question_sets_col.update_one(
            {"questions.question_id": question_id, "questions.options.option_id": option_id},
            {"$set": {"questions.$[question].options.$[option].explanation_image": binary_image}},
            array_filters=[{"question.question_id": question_id}, {"option.option_id": option_id}]
        )
    print(f"Option {option_id} in question {question_id} image updated successfully.")

def store_assets(image_name, image_path):
    with open(image_path, 'rb') as image_file:
        image_data = image_file.read()
        binary_image = Binary(image_data)
        assets_col.update_one(
            {"filename": image_name,},
            {"$set": {"data": binary_image}}
        )
    print(f"Image {image_name} in asset image updated successfully.")

def insert_assets(file_path, filename, filetype):
    with open(file_path, 'rb') as file:
        binary_data = Binary(file.read())
    
    asset_document = {
        "filename": filename,
        "filetype": filetype,
        "data": binary_data
    }
    
    assets_col.insert_one(asset_document)
    print(f"Inserted {filename} into the assets collection.")



# # Example usage
# store_image("3", "asset/asset-telebanner-09.png")

# # Example usage
# store_option_image(question_id='3', option_id='1', image_path="asset/asset-telebanner-10.png")

# # Example usage
# store_assets("badge_silhouette", image_path="asset/asset-telebanner-02.png")

# # Example usage
# insert_assets('asset/badge_1star.png', 'badge_1star', 'image/png')
# insert_assets('asset/badge_2star.png', 'badge_2star', 'image/png')
# insert_assets('asset/badge_3star.png', 'badge_3star', 'image/png')