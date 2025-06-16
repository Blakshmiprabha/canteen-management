from pymongo import MongoClient
from bson.objectid import ObjectId
import os

# Connect to MongoDB
client = MongoClient(os.environ.get("MONGO_URI", "mongodb://localhost:27017/"))
db = client['canteen_db']  # Your DB name

# Define collections
menu_collection = db['menu']
orders_collection = db['orders']
users_collection = db['users']

# Helper functions (already used in app.py)
def get_user_by_email(email):
    return users_collection.find_one({"email": email})

def insert_user(user_data):
    return users_collection.insert_one(user_data)

def get_menu_items():
    return list(menu_collection.find())

def insert_order(order_data):
    return orders_collection.insert_one(order_data).inserted_id

def get_orders_by_user(user_email):
    return list(orders_collection.find({"user_email": user_email}))

def update_menu_item(item_id, name, price):
    return menu_collection.update_one(
        {"_id": ObjectId(item_id)},
        {"$set": {"name": name, "price": price}}
    )

def update_order_status(order_id, status):
    return orders_collection.update_one(
        {"_id": ObjectId(order_id)},
        {"$set": {"status": status}}
    )
