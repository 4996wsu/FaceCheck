#   -------------------------------------------------------------------------------------------------
#
#   This file handles all the database functions involving Firebase.
#
#   -------------------------------------------------------------------------------------------------
import torch
import requests
from io import BytesIO
import firebase_admin
from firebase_admin import credentials, firestore, storage
from google.cloud.firestore_v1.base_query import FieldFilter, Or
from pathlib import Path
import tempfile
import cv2
from datetime import datetime
from preprocess import detect_and_crop_face, face_encode, make_pt_file
import torch
# from preprocess import encode_face


#  Connect to firebase db
cred_fp = str(Path.cwd()) + "\db_credentials.json"
cred = credentials.Certificate(cred_fp)
firebase_admin.initialize_app(cred, {'storageBucket': 'facecheck-93450.appspot.com'})

#  Other common variables
db = firestore.client()
collectionName = "infoCollection"
class_doc = "class_doc"
student_doc = "student_doc"
user_doc = "user_doc"


#  ------------------------------  MAIN FUNCTIONALITY  ------------------------------
#  Reset document in Firebase
def reset_docs():
    dataClass = {
        'classes': {
            'CSC_4996_001': {
                'professor': 'mousavi',
                'class_encoding': 'NO ENCODING',
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
                },
                'hi4718': {
                    'picture': 'NO PHOTO',
                    'attendance': {
                        '02_06_2024': {
                            '17_30_00': False,
                            '17_35_00': False
                        },
                        '02_08_2024': {
                            '17_30_00': True,
                            '17_35_00': True
                        } 
                    }
                },
                'hi6576': {
                    'picture': 'NO PHOTO',
                    'attendance': {
                        '02_06_2024': {
                            '17_30_00': True,
                            '17_35_00': False
                        },
                        '02_08_2024': {
                            '17_30_00': False,
                            '17_35_00': False
                        } 
                    }
                }
            }
        }
    }
    dataUser = {
        'users': {
            'hc9082': {
                'picture': 'NO PHOTO',
                'encoding': 'NO ENCODING',
                'professor': False,
                'audit log': {
                    '02_12_2024': ['21_18_00', "Updated photo"]
                }
            },
            'hi4718': {
                'picture': 'NO PHOTO',
                'encoding': 'NO ENCODING',
                'professor': False,
                'audit log': {
                    '02_12_2024': ['21_18_00', "Updated photo"]
                }
            },
            'hi6576': {
                'picture': 'NO PHOTO',
                'encoding': 'NO ENCODING',
                'professor': False,
                'audit log': {
                    '02_12_2024': ['21_18_00', "Updated photo"]
                }
            },
            'mousavi': {
                'picture': 'NO PHOTO',
                'encoding': 'NO ENCODING',
                'professor': True,
                'audit log': {
                    '02_16_2024': ['12_35_00', "Changed password"]
                }
            }
        }
    }

    doc_ref = db.collection(collectionName)
    doc_ref.document(class_doc).delete()
    doc_ref.document(student_doc).delete()
    doc_ref.document(user_doc).delete()
    doc_ref.document(class_doc).set(dataClass)
    doc_ref.document(student_doc).set(dataStudent)
    doc_ref.document(user_doc).set(dataUser)
    
    update_student_photo('hc9082', 'photos/hc9082/hc9082.jpg')
    update_student_photo('hi4718', 'photos/hi4718/hi4718.jpg')
    update_student_photo('hi6576', 'photos/hi6576/hi6576.jpg')

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
    
#  Add new student to class
def add_student(section, name):
    student_dict = get_doc(student_doc)
    
    if lookup(name, student_dict) != None:
        print("Error: Cannot add user '" + name + "' because the user already exists.")
    else:
        studentKey = 'students.' + section + '.' + name + '.picture'
        update_doc(student_doc, studentKey, "NO PHOTO")
        userKey = 'users.' + name + '.picture'
        update_doc(user_doc, userKey, "NO PHOTO")
        userKey = 'users.' + name + '.encoding'
        update_doc(user_doc, userKey, "NO ENCODING")
        
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
        print("Student '" + name + " marked as " + str(value) + " on " + date + " at " + time + ".")




#  Update student photo
def update_student_photo(name, file):
    bucket = storage.bucket()
    imageBlob = bucket.blob(name + "_photo")
    imageBlob.make_public()
    name_list = [name]
    
    # Crop student photo & upload encoding
    cropped_image = detect_and_crop_face(file)
    if cropped_image is not None:
        # Save cropped photo to temporary location and upload
        with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as temp_file:
            cv2.imwrite(temp_file.name, cropped_image)
            imageBlob.upload_from_filename(temp_file.name)
            
        # Save encoding to temporary location and upload
        embedding_link = make_pt_file(face_encode(cropped_image,device=torch.device('cuda' if torch.cuda.is_available() else 'cpu')), name_list)
        
        # Upload photo and encoding      
        userPhotoKey = 'users.' + name + '.picture'
        update_doc(user_doc, userPhotoKey, imageBlob.public_url)
        userEncodingKey = 'users.' + name + '.encoding'
        update_doc(user_doc, userEncodingKey, embedding_link)
        print("Face uploaded.")
    else:
        print("Error: No face detected, or there was an error processing the image.")
        
    
#  Remove student photo
def remove_student_photo(name):
    bucket = storage.bucket()
    blob = bucket.blob(name + "_photo")
    if blob.exists():
        blob.delete()

        # Remove photo and encoding
        userKey = 'users.' + name + '.picture'
        update_doc(user_doc, userKey, "NO PHOTO")
        print("Photo for '" + name + "' deleted successfully.")
        
        # Add encoding removal here
    else:
        print("Error: Student '" + name + "', if they exist, has no photo in the database.")


# Retrieve file from Firebase storage (filetype is 'picture' or 'encoding')
def retrieve_file(name, filetype): 
    doc = get_doc(user_doc)

    # Debug message
    if (doc['users'][name][filetype] == 'NO ENCODING'):
        print("Error: Cannot retrieve filetype '" + filetype + "' for user '" + name + "'.")
    else:
        print("Retrieved filetype '" + filetype + "' for user '" + name + "'.")
        
    return doc['users'][name][filetype]

# Retrieve class embedding file from Firebase storage
def retrieve_class_embedding(section): 
    doc = get_doc(class_doc)

    # Debug message
    if (doc['classes'][section]['class_encoding'] == 'NO ENCODING'):
        print("Error: Cannot retrieve filetype class encoding for class '" + section + "'.")
    else:
        print("Retrieved class encoding for class '" + section + "'.")
    print(doc['classes'][section]['class_encoding'])
    return doc['classes'][section]['class_encoding']


# Retrieve array of names for all students in a class section
def retrieve_names_from_class(section): 
    doc = get_doc(student_doc)    
    return list(doc['students'][section].keys())
    
import numpy as np 
# Retrieve all encodings for a class section
def retrieve_encodings_from_class(section):
    names = retrieve_names_from_class(section)
    encoding_list = []
    for name in names:
        retrieved_encoding = retrieve_file(name, 'encoding')
        if retrieved_encoding != 'NO ENCODING':
            encoding_list.append(retrieved_encoding)
    print(encoding_list)
    return encoding_list 


def download_pt_file_student(url):
    response = requests.get(url)
    response.raise_for_status()
    buffer = BytesIO(response.content)
    embedding, name = torch.load(buffer, map_location='cpu')
    return embedding[0], name[0]

def update_class_encoding(section, file):
    bucket = storage.bucket()
    blob = bucket.blob(section + ".pt")
    blob.upload_from_filename(file)
    blob.make_public()

    # Upload
    key = 'classes.' + section + '.class_encoding'
    update_doc(class_doc, key, blob.public_url)

def combine_pt_files(section):
    combined_embedding_list = []
    combined_name_list = []

    urls = retrieve_encodings_from_class(section)
    for url in urls:
        embedding, name = download_pt_file_student(url)
        combined_embedding_list.append(embedding)
        combined_name_list.append(name)
    print(combined_embedding_list)
    combined_data = {'embedding_list': combined_embedding_list, 'name_list': combined_name_list}
    torch.save([combined_embedding_list,combined_name_list], f'{section}.pt')
    update_class_encoding(section, f'{section}.pt')


def download_file_combine(url, section):
    with requests.get(url, stream=True) as response:
        response.raise_for_status()
        with open(section, 'wb') as file:
            for chunk in response.iter_content(chunk_size=8192):
                file.write(chunk)
    
    print(f"File downloaded and saved as {section}")

def get_low_attendance_students(section):
    doc = get_doc('student_doc')
    if doc is None:  
        print("No document found")
        return []
    students = doc['students'].get(section, {})  
    low_attendance_students = []
    for student_id, student_data in students.items():
        if student_id == 'class_photos':
            continue
        total_sessions = 0
        attended_sessions = 0
        for date, sessions in student_data['attendance'].items():
            for _, attended in sessions.items():
                total_sessions += 1
                if attended:
                    attended_sessions += 1
        attendance_rate = (attended_sessions / total_sessions) * 100 if total_sessions > 0 else 0
        print(student_id,attended_sessions)
        if attendance_rate <= 50:  
            low_attendance_students.append(student_id)
    return low_attendance_students


# Example usage
section = 'CSC_4996_001_W_2024'
#low_attendance_students = get_low_attendance_students(section)
#print("Students with <= 10% attendance:", low_attendance_students)
#  ------------------------------  TESTING CODE  ------------------------------
print("---------------------- START DATABASE TESTING ----------------------")
#reset_docs()
# section='CSC_4996_001'
# retrieve_class_embedding(section)
# retrieve_encodings_from_class('CSC_4996_001')
#combine_pt_files('CSC_4996_001')
# get_all_docs()

# update_doc(student_doc, 'students.CSC_4996_001.hc9082.attendance.02_08_2024.17_40_00', True)
# add_student('CSC_4996_001', 'hi6576')
# update_student_attendance('CSC_4996_001', 'hc9082', True, '02_08_2024', '17_40_00')
# update_student_attendance('CSC_4996_001', 'hc9082', True)
# update_student_photo('hc9082', 'photos/hc9082/hc9082.jpg')
# update_student_photo('hi4718', 'photos/hi4718/hi4718.jpg')
# update_student_photo('hi6576', 'photos/hi6576/hi6576.jpg')
# remove_student_photo('hc9082')
# remove_student_photo('hc9082')

# add_student('CSC_4996_004', 'hc2810')
# add_class('CSC_4996_001', 'mousavi')
# add_class('CSC_4996_004', 'mousavi')

# print(retrieve_file('hc9082', 'picture'))
# print(retrieve_names())
#retrieve_encodings_from_class('CSC_4996_001')

print("---------------------- END DATABASE TESTING ----------------------")