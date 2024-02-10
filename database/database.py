import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore
from pathlib import Path

cred_fp = str(Path.cwd()) + "\database\db_credentials.json"
cred = credentials.Certificate(cred_fp)
firebase_admin.initialize_app(cred)

db = firestore.client()

data = {
    'key': 'value'
}

doc_ref = db.collection('name').document()
doc_ref.set(data)

print("Document ID: ", doc_ref.id)