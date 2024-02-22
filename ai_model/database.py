#   -------------------------------------------------------------------------------------------------
#
#   This file handles all the database functions involving Firebase.
#
#   -------------------------------------------------------------------------------------------------

import firebase_admin
from firebase_admin import credentials, firestore, storage
from google.cloud.firestore_v1.base_query import FieldFilter, Or
from pathlib import Path
import tempfile
import cv2
from datetime import datetime
from preprocess import detect_and_crop_face


#  Connect to firebase db
cred_fp = str(Path.cwd()) + "\db_credentials.json"
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
                    'picture': 'NO PHOTO',
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


#  Get current date and time
def getDate():
    now = datetime.now()
    return now.strftime("%m_%d_%Y")

def getTime():
    now = datetime.now()
    return now.strftime("%H_%M_%S")
    
       
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
        print("Student '" + name + "' successfully added.")
   
    
#  ------------------------------  SHORTCUT FUNCTIONS  ------------------------------
#  Update student attendance
def update_student_attendance(section, name, value, date = getDate(), time = getTime()):
    student_dict = get_doc(student_doc)
    
    if lookup(name, student_dict) == None:
        print("Error: Cannot update attendance for '" + name + "' because the user does not exist.")
    else:
        key = 'students.' + section + '.' + name + '.attendance.' + date + '.' + time
        update_doc(student_doc, key, value)
        print("Student '" + name + "' marked as present on " + date + " at " + time + ".")

#  Update student photo
def update_student_photo(section, name, file):
    bucket = storage.bucket()
    filename = section + '_' + name
    blob = bucket.blob(filename)
    
    cropped_image = detect_and_crop_face(file)
    if cropped_image is not None:
        with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as temp_file:
            cv2.imwrite(temp_file.name, cropped_image)
            blob.upload_from_filename(temp_file.name)
        key = 'students.' + section + '.' + name + '.picture'
        update_doc(student_doc, key, blob.public_url)
    else:
        print("Error: No face detected, or there was an error processing the image.")
        
    
#  Remove student photo
def remove_student_photo(section, name, file):
    bucket = storage.bucket()
    filename = section + '_' + name
    blob = bucket.blob(filename)
    if blob.exists():
        blob.delete()
        key = 'students.' + section + '.' + name + '.picture'
        update_doc(student_doc, key, "NO PHOTO")
        print("Photo for '" + name + "' deleted successfully.")
    else:
        print("Error: Student '" + name + "', if they exist, has no photo in the database.")


#  ------------------------------  TESTING CODE  ------------------------------
print("---------------------- START DATABASE TESTING ----------------------")

#reset_docs()
#get_all_docs()

#update_doc(student_doc, 'students.CSC_4996_001.hc9082.attendance.02_08_2024.17_40_00', True)
add_student('CSC_4996_001', 'hi4718')
update_student_attendance('CSC_4996_001', 'hc9082', True, '02_08_2024', '17_40_00')
update_student_attendance('CSC_4996_001', 'hc9082', True)
update_student_photo('CSC_4996_001', 'hc9082', 'photos/hc9082/hc9082.jpg')
# remove_student_photo('CSC_4996_001', 'hc9082', 'C:/Users/aafna/Desktop/photo.jpeg')
# remove_student_photo('CSC_4996_001', 'hc9082', 'C:/Users/aafna/Desktop/photo.jpeg')

add_student('CSC_4996_004', 'hc2810')
add_class('CSC_4996_001', 'mousavi')
add_class('CSC_4996_004', 'mousavi')

print("---------------------- END DATABASE TESTING ----------------------")