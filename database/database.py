#   -------------------------------------------------------------------------------------------------
#
#   This file handles all the database functions involving Firebase.
#
#   -------------------------------------------------------------------------------------------------

import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore
from google.cloud.firestore_v1.base_query import FieldFilter, Or
from pathlib import Path


#  Connect to firebase db
cred_fp = str(Path.cwd()) + "\database\db_credentials.json"
cred = credentials.Certificate(cred_fp)
firebase_admin.initialize_app(cred)

#  Other common variables
db = firestore.client()
collectionName = "infoCollection"
class_doc = "GmqCfAAPxope9LYsnAI1"


#  Create document in Firebase
def create_new_doc():
    data = {
        'key': 'value'
    }

    doc_ref = db.collection(collectionName).document()
    doc_ref.set(data)

    print("Document ID: ", doc_ref.id)
    

#  Retrieve all docs in collection
def get_all_docs():
    docs = (
        db.collection(collectionName)
        .stream()
    )
    
    # Iterate over documents and store their IDs and data into a list
    doc_list = []
    for doc in docs:
        doc_data = doc.to_dict()
        doc_data['id'] = doc.id
        doc_data['data'] = doc._data
        doc_list.append(doc_data)
        
    # Print all documents in the list
    for doc_data in doc_list:
        print(f"Document ID: {doc_data['id']}")
        print(f"Document Data: {doc_data['data']}")
        print()


#  Retrieve doc in Firebase
def get_doc(doc_id):
    doc_ref = db.collection(collectionName).document(doc_id)
    doc = doc_ref.get()
    if doc.exists:
        return doc.to_dict()
    else:
        print(f"Document {doc_id} not found in {collectionName}.")
        return None
       
       
# Update existing document
def update_doc():
    print("Cannot update doc")
    

#  Code to execute
get_all_docs()