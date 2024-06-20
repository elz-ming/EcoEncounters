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

def store_image(difficulty, question_id, image_path):
    with open(image_path, 'rb') as image_file:
        image_data = image_file.read()
        question_sets_col.update_one(
            {"difficulty": difficulty,"questions.question_id": question_id},
            {"$set": {"questions.$.image": Binary(image_data)}}
        )
    print(f"Question {question_id} image updated successfully.")

def store_option_image(difficulty, question_id, option_id, image_path):
    with open(image_path, 'rb') as image_file:
        image_data = image_file.read()
        binary_image = Binary(image_data)
        question_sets_col.update_one(
            {"difficulty": difficulty, "questions.question_id": question_id, "questions.options.option_id": option_id},
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

def move_and_update_question_id(from_difficulty, to_difficulty, question_id, new_question_id):
    # Find the question to move
    from_set = question_sets_col.find_one({"difficulty": from_difficulty, "questions.question_id": question_id})
    if not from_set:
        print(f"No question with ID {question_id} found in {from_difficulty} difficulty.")
        return

    question = None
    for q in from_set["questions"]:
        if q["question_id"] == question_id:
            question = q
            break

    if not question:
        print(f"No question with ID {question_id} found.")
        return

    # Remove the question from the original set
    question_sets_col.update_one(
        {"difficulty": from_difficulty},
        {"$pull": {"questions": {"question_id": question_id}}}
    )

    # Update the question_id
    question['question_id'] = new_question_id

    # Add the question to the new set
    question_sets_col.update_one(
        {"difficulty": to_difficulty},
        {"$push": {"questions": question}}
    )

    print(f"Question {question_id} moved from {from_difficulty} to {to_difficulty} and updated to ID {new_question_id}.")

def remove_mode_functionality():
    users_col = db.users

    # Remove difficulty field from user documents
    users_col.update_many({}, {"$unset": {"difficulty": ""}})

    # Remove difficulty related commands from bot script
    # This would involve manually editing the bot script to remove /mode and related functionality
    print("Difficulty field removed from user documents. Please manually update the bot script to remove /mode and related functionality.")

# # Example usage
# store_image(difficulty="Intermediate", question_id="1", image_path="asset/asset-telebanner-03.png")
# store_image(difficulty="Intermediate", question_id="2", image_path="asset/asset-telebanner-09.png")
# store_image(difficulty="Intermediate", question_id="3", image_path="asset/asset-telebanner-02.png")

# # Example usage
# store_option_image(difficulty="Intermediate", question_id='1', option_id='1', image_path="asset/asset-telebanner-05.png")
# store_option_image(difficulty="Intermediate", question_id='1', option_id='3', image_path="asset/asset-telebanner-06.png")
# store_option_image(difficulty="Intermediate", question_id='1', option_id='4', image_path="asset/asset-telebanner-07.png")
# store_option_image(difficulty="Intermediate", question_id='1', option_id='2', image_path="asset/asset-telebanner-04.png")

# store_option_image(difficulty="Intermediate", question_id='2', option_id='1', image_path="asset/asset-telebanner-10.png")

# store_option_image(difficulty="Intermediate", question_id='3', option_id='4', image_path="asset/asset-telebanner-11.png")

# # Example usage
# store_assets("badge_silhouette", image_path="asset/asset-telebanner-02.png")

# # Example usage
# insert_assets('asset/badge_1star.png', 'badge_1star', 'image/png')
# insert_assets('asset/badge_2star.png', 'badge_2star', 'image/png')
# insert_assets('asset/badge_3star.png', 'badge_3star', 'image/png')

# # Example usage
move_and_update_question_id(from_difficulty="Intermediate", to_difficulty="Easy", question_id="3", new_question_id="4")

# # Example usage
remove_mode_functionality()