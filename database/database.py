#   -------------------------------------------------------------------------------------------------
#
#   This file handles all the database functions involving Firebase.
#
#   -------------------------------------------------------------------------------------------------

import firebase_admin
from firebase_admin import credentials, firestore, storage
from google.cloud.firestore_v1.base_query import FieldFilter, Or
from pathlib import Path


#  Connect to firebase db
cred_fp = str(Path.cwd()) + "\database\db_credentials.json"
cred = credentials.Certificate(cred_fp)
firebase_admin.initialize_app(cred, {'storageBucket': 'facecheck-93450.appspot.com'})

#  Other common variables
db = firestore.client()
collectionName = "infoCollection"
class_doc = "class_doc"
student_doc = "student_doc"


#  ------------------------------  MAIN FUNCTIONALITY  ------------------------------
#  Reset document in Firebase
def reset_docs():
    dataClass = {
        'classes': {
            'CSC_4996_001': {
                'professor': 'mousavi',
                'schedule': {
                    'Tuesday': ['17_30', '18_45'],
                    'Thursday': ['17_30', '20_40']
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
    doc_ref.document(class_doc).delete()
    doc_ref.document(student_doc).delete()
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
    
    
#  Recursively search dictionary
def lookup(key, data):
    if key in data:
        return data[key]
    for value in data.values():
        if isinstance(value, dict):
            return lookup(key, value)
    return None
    
       
#  Update existing document
def update_doc(doc_id, key, value):
    doc_ref = db.collection(collectionName).document(doc_id)
    doc_ref.update({
        key: value
    })

#  Add new class section
def add_class(section, prof):
    class_dict = get_doc(class_doc)
    
    if lookup(section, class_dict) != None:
        print("Error: Cannot add class '" + section + "' because the class already exists.")
    else:
        key = 'classes.' + section + '.professor'
        update_doc(class_doc, key, prof)
        print("Class '" + section + "' successfully added.")
    
#  Add new student
def add_student(section, name):
    student_dict = get_doc(student_doc)
    
    if lookup(name, student_dict) != None:
        print("Error: Cannot add user '" + name + "' because the user already exists.")
    else:
        key = 'students.' + section + '.' + name + '.picture'
        update_doc(student_doc, key, "NO PHOTO")
        print("User '" + name + "' successfully added.")
   
    
#  ------------------------------  SHORTCUT FUNCTIONS  ------------------------------
#  Update student attendance
def update_student_attendance(section, name, date, time, value):
    key = 'students.' + section + '.' + name + '.attendance.' + date + '.' + time
    update_doc(student_doc, key, value)

#  Update student photo
def update_student_photo(section, name, file):
    bucket = storage.bucket()
    filename = section + '_' + name
    blob = bucket.blob(filename)
    blob.upload_from_filename(file)
    #blob.make_public()
    
    # Update database
    key = 'students.' + section + '.' + name + '.picture'
    update_doc(student_doc, key, blob.public_url)


#  ------------------------------  TESTING CODE  ------------------------------
reset_docs()
get_all_docs()
#update_doc(student_doc, 'students.CSC_4996_001.hc9082.attendance.02_08_2024.17_40_00', True)
update_student_attendance('CSC_4996_001', 'hc9082', '02_08_2024', '17_40_00', True)
update_student_photo('CSC_4996_001', 'hc9082', 'C:/Users/aafna/Desktop/photo.jpeg')
add_student('CSC_4996_004', 'hc2810')
add_student('CSC_4996_001', 'hc9082')
add_class('CSC_4996_001', 'mousavi')
add_class('CSC_4996_004', 'mousavi')