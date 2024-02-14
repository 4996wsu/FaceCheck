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
class_doc = "class_doc"
student_doc = "student_doc"


#  Reset document in Firebase
def reset_docs():
    dataClass = {
        'classes': {
            'CSC_4996_001': {
                'professor': 'mousavi',
                'schedule': {
                    'Tuesday': ['17_30', '18_45'],
                    'Wednesday': ['17_30', '20_40']
                }
            }
        } 
    }
    dataStudent = {
        'students': {
            'CSC_4996_001': {
                'hc9082': {
                    'picture': 'URL HERE',
                    'attendance': {
                        '02_06_2024': {
                            '17_30_00': True,
                            '17_35_00': True
                        },
                        '02_08_2024': {
                            '17_30_00': True,
                            '17_35_00': False
                        } 
                    }
                }
            }
        }
    }

    doc_ref = db.collection(collectionName)
    doc_ref.document(class_doc).set(dataClass)
    doc_ref.document(student_doc).set(dataStudent)

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


#  Retrieve document from database and return as a dictionary
def get_doc(doc_id):
    doc_ref = db.collection(collectionName).document(doc_id)
    doc = doc_ref.get()
    if doc.exists:
        return doc.to_dict()
    else:
        print(f"Document {doc_id} not found in {collectionName}.")
        return None
       
       
#  Update existing document
def update_doc(doc_id, key, value):
    doc_ref = db.collection(collectionName).document(doc_id)
    doc_ref.update({
        key: value
    })
    
#  Update student attendance
def update_student_attendance(section, name, date, time, value):
    key = 'students.' + section + '.' + name + '.attendance.' + date + '.' + time
    update_doc(student_doc, key, value)

def update_student_photo(section, name, value):
    key = 'students.' + section + '.' + name + '.picture'
    update_doc(student_doc, key, value)


#  Code to execute
reset_docs()
get_all_docs()
#update_doc(student_doc, 'students.CSC_4996_001.hc9082.attendance.02_08_2024.17_40_00', True)
update_student_attendance('CSC_4996_001', 'hc9082', '02_08_2024', '17_40_00', True)
update_student_photo('CSC_4996_001', 'hc9082', 'UPDATED IMAGE URL')