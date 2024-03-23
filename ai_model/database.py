#   -------------------------------------------------------------------------------------------------
#
#   This file handles all the database functions involving Firebase for the DESKTOP APP.
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
            'CSC_4996_001_W_2024': {
                'class_name': 'Senior Capstone Project Section 001',
                'professor': 'dx6565',
                'class_encoding': 'NO ENCODING',
                'class_encoding_update': False,
                'schedule': {
                    'Tuesday': ['17_30', '18_45'],
                    'Thursday': ['17_30', '20_40']
                }
            },
            'CSC_4500_002_S_2024': {
                'class_name': 'Theoretical Computer Science Section 002',
                'professor': 'dx6565',
                'class_encoding': 'NO ENCODING',
                'class_encoding_update': False,
                'schedule': {
                    'Monday': ['17_00', '19_30'],
                }
            }
        } 
    }
    dataStudent = {
        'students': {
            'CSC_4996_001_W_2024': {
                'hc9082': {
                    'picture_status': 'Pending',
                    'attendance': {
                        '00_00_0000': {
                            '00_00_00': True,
                            'Overall': True
                        },
                        '03_05_2024': {
                            '17_30_00': True,
                            '17_35_00': True,
                            'Overall': True
                        },
                        '03_07_2024': {
                            '17_30_00': True,
                            '17_35_00': False,
                            'Overall': True
                        } 
                    }
                },
                'hi4718': {
                    'picture_status': 'Pending',
                    'attendance': {
                        '00_00_0000': {
                            '00_00_00': True,
                            'Overall': True
                        },
                        '03_05_2024': {
                            '17_30_00': False,
                            '17_35_00': False,
                            'Overall': False
                        },
                        '03_07_2024': {
                            '17_30_00': True,
                            '17_35_00': True,
                            'Overall': True
                        } 
                    }
                },
                'hi6576': {
                    'picture_status': 'Pending',
                    'attendance': {
                        '00_00_0000': {
                            '00_00_00': True,
                            'Overall': True
                        },
                        '03_05_2024': {
                            '17_30_00': True,
                            '17_35_00': False,
                            'Overall': True
                        },
                        '03_07_2024': {
                            '17_30_00': False,
                            '17_35_00': False,
                            'Overall': False
                        } 
                    }
                },
                'class_photos': {
                    '00_00_0000': {
                        '00_00_00': 'NO PHOTO'
                    },
                    '03_05_2024': {
                        '17_30_00': 'NO PHOTO',
                        '17_35_00': 'NO PHOTO'
                    },
                    '03_07_2024': {
                        '17_30_00': 'NO PHOTO',
                        '17_35_00': 'NO PHOTO'
                    }
                }
            },
            'CSC_4500_002_S_2024': {
                'hc9082': {
                    'picture_status': 'Pending',
                    'attendance': {
                        '00_00_0000': {
                            '00_00_00': True,
                            'Overall': True
                        },
                        '03_04_2024': {
                            '17_30_00': True,
                            '17_35_00': True,
                            'Overall': True
                        },
                        '03_11_2024': {
                            '17_30_00': True,
                            '17_35_00': False,
                            'Overall': True
                        } 
                    }
                },
                'hi4718': {
                    'picture_status': 'Pending',
                    'attendance': {
                        '00_00_0000': {
                            '00_00_00': True,
                            'Overall': True
                        },
                        '03_04_2024': {
                            '17_30_00': False,
                            '17_35_00': False,
                            'Overall': False
                        },
                        '03_11_2024': {
                            '17_30_00': True,
                            '17_35_00': True,
                            'Overall': True
                        } 
                    }
                },
                'hi6576': {
                    'picture_status': 'Pending',
                    'attendance': {
                        '00_00_0000': {
                            '00_00_00': True,
                            'Overall': True
                        },
                        '03_04_2024': {
                            '17_30_00': True,
                            '17_35_00': False,
                            'Overall': True
                        },
                        '03_11_2024': {
                            '17_30_00': False,
                            '17_35_00': False,
                            'Overall': False
                        } 
                    }
                },
                'class_photos': {
                    '00_00_0000': {
                        '00_00_00': 'NO PHOTO'
                    },
                    '03_04_2024': {
                        '17_30_00': 'NO PHOTO',
                        '17_35_00': 'NO PHOTO'
                    },
                    '03_11_2024': {
                        '17_30_00': 'NO PHOTO',
                        '17_35_00': 'NO PHOTO'
                    }
                }
            }
        }
    }
    dataUser = {
        'users': {
            'hc9082': {
                'fname': 'Aafnan',
                'lname': 'Mahmood',
                'picture': 'NO PHOTO',
                'encoding': 'NO ENCODING',
                'role': 'student',
                'audit log': {
                    '02_12_2024': ['21_18_00', "Updated photo"]
                }
            },
            'hi4718': {
                'fname': 'Ahmed',
                'lname': 'Minhaj',
                'picture': 'NO PHOTO',
                'encoding': 'NO ENCODING',
                'role': 'student',
                'audit log': {
                    '02_12_2024': ['21_18_00', "Updated photo"]
                }
            },
            'hi6576': {
                'fname': 'Mohamad',
                'lname': 'Hachem',
                'picture': 'NO PHOTO',
                'encoding': 'NO ENCODING',
                'role': 'student',
                'audit log': {
                    '02_12_2024': ['21_18_00', "Updated photo"]
                }
            },
            'dx6565': {
                'fname': 'Seyed Ziae',
                'lname': 'Mousavi Mojab',
                'picture': 'NO PHOTO',
                'encoding': 'NO ENCODING',
                'role': 'professor',
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
    update_class_encoding_status('CSC_4996_001_W_2024', true)
    update_class_encoding_status('CSC_4500_002_S_2024', true)
    add_student('hz2948', 'John', 'Doe', 'student')

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
    
#  Add new student to **DATABASE**
def add_student(accessid, fname, lname, role):
    user_dict = get_doc(user_doc)
    
    if lookup(accessid, user_dict) != None:
        print("Error: Cannot add user '" + accessid + "' because the user already exists.")
    else:
        key = 'users.' + accessid + '.fname'
        update_doc(user_doc, key, fname)
        key = 'users.' + accessid + '.lname'
        update_doc(user_doc, key, lname)
        key = 'users.' + accessid + '.picture'
        update_doc(user_doc, key, "NO PHOTO")
        key = 'users.' + accessid + '.encoding'
        update_doc(user_doc, key, "NO ENCODING")
        key = 'users.' + accessid + '.role'
        update_doc(user_doc, key, role)
        log_arr = [getTime(), "Created account"]
        key = 'users.' + accessid + '.audit_log.' + getDate()
        update_doc(user_doc, key, log_arr)
        
        print("Student '" + accessid + "' successfully added.")
        
#  Add new student to **CLASS**
def add_student_to_class(section, accessid):
    student_dict = get_doc(student_doc)
    user_dict = get_doc(user_doc)
    
    if lookup(accessid, student_dict['students'][section]) != None:
        print("Error: Cannot add user '" + accessid + "' because the user is already in " + section + ".")
    elif lookup(accessid, user_dict) == None:
        print("Error: Cannot add user '" + accessid + "' because the user does not exist.")
    else:
        key = 'students.' + section + '.' + accessid + '.attendance.00_00_0000.00_00_00'
        update_doc(student_doc, key, True)
        classKey = 'classes.' + section + '.encoding_update'
        update_doc(class_doc, classKey, True)
        
        print("Student '" + accessid + "' successfully added to " + section + ".")
   
    
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

#  Update a student's overall attendance
def update_overall_attendance(section, name, value, date = getDate()):
    student_dict = get_doc(student_doc)
    
    if lookup(name, student_dict) == None:
        print("Error: Cannot update overall attendance for '" + name + "' because the user does not exist.")
    else:
        key = 'students.' + section + '.' + name + '.attendance.' + date + '.Overall'
        update_doc(student_doc, key, value)
        print("Student '" + name + " marked as " + str(value) + " OVERALL on " + date + ".")

#  Update student photo
def update_student_photo(name, file):
    bucket = storage.bucket()
    imageBlob = bucket.blob(name + "_photo")
    name_list = [name]
    
    # Crop student photo & upload encoding
    cropped_image = detect_and_crop_face(file)
    if cropped_image is not None:
        # Save cropped photo to temporary location and upload
        with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as temp_file:
            cv2.imwrite(temp_file.name, cropped_image)
            imageBlob.upload_from_filename(temp_file.name)
        imageBlob.make_public()
            
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


#  Update class photo
def update_class_photo(section, frame, date = getDate(), time = getTime()):
    bucket = storage.bucket()
    imageBlob = bucket.blob(section + "/" + date + "/" + time + "_photo")
    
    # Crop student photo & upload encoding
    with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as temp_file:
        cv2.imwrite(temp_file.name, frame)
        imageBlob.upload_from_filename(temp_file.name)
    imageBlob.make_public()
        
    # Upload photo and encoding      
    key = 'students.' + section + '.class_photos.' + date + '.' + time
    update_doc(student_doc, key, imageBlob.public_url)
    print("Class photo uploaded for" + date + " at " + time + ".")


# Update photo status for professor to approve        
def update_photo_status(section, name, value):
    user_dict = get_doc(user_doc)
    student_dict = get_doc(student_doc)
    
    if lookup(name, user_dict) == None:
        print("Error: Cannot update photo status for '" + name + "' because the user does not exist.")
    elif lookup(name, student_dict['students'][section]) == None:
        print("Error: Cannot update photo status for '" + name + "' because the user is not in class '" + section + "'.")
    else:
        key = 'students.' + section + '.' + name + '.picture_status'
        print("Updated photo status for '" + name + "' in class '" + section + "'.")
        update_doc(student_doc, key, value)

# Update photo status for professor to approve (AS A BATCH)   
def update_photo_status_batch(name, value):
    user_dict = get_doc(user_doc)
    student_dict = get_doc(student_doc)
    
    if lookup(name, user_dict) == None:
        print("Error: Cannot update photo status for '" + name + "' because the user does not exist.")
    else:
        for section in student_dict['students']:
            if lookup(name, student_dict['students'][section]) == None:
                print("Error: Cannot update photo status for '" + name + "' because the user is not in class '" + section + "'.")
            else:
                key = 'students.' + section + '.' + name + '.picture_status'
                print("Updated photo status for '" + name + "' in class '" + section + "'.")
                update_doc(student_doc, key, value)
    

#  Remove student photo
def remove_student_photo(name):
    bucket = storage.bucket()
    blob = bucket.blob(name + "_photo")
    if blob.exists():
        blob.delete()

        # Remove photo and encoding
        userKey = 'users.' + name + '.picture'
        update_doc(user_doc, userKey, "NO PHOTO")
        userKey = 'users.' + name + '.encoding'
        update_doc(user_doc, userKey, "NO ENCODING")
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
    names = list(doc['students'][section].keys()) 
    
    # Remove class_photos from names since it is not an actual student
    if "class_photos" in names:
        names.remove("class_photos")
     
    # Remove students who do not have an approved photo
    final_name_list = []
    for name in names:
        if doc['students'][section][name]['picture_status'] == "Accepted":
            final_name_list.append(name)
        
    return final_name_list
    
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

#  Update class encoding
def update_class_encoding(section, file):
    doc = get_doc(class_doc)
    if doc['classes'][section]['class_encoding_update'] == True:
        bucket = storage.bucket()
        blob = bucket.blob(section + ".pt")
        blob.upload_from_filename(file)
        blob.make_public()
        # Update encoding status to show encoding update is no longer needed
        update_class_encoding_status(section, False)

        # Upload
        key = 'classes.' + section + '.class_encoding'
        update_doc(class_doc, key, blob.public_url)
    else:
        print("Error: Encoding update is not needed for '" + section + "'.")

# Set flag that class encoding needs update
def update_class_encoding_status(section, value):
    key = 'classes.' + section + '.class_encoding_update'
    update_doc(class_doc, key, value)


def combine_pt_files(section):
    combined_embedding_list = []
    combined_name_list = []

    urls = retrieve_encodings_from_class(section)
    for url in urls:
        embedding, name = download_pt_file_student(url)
        combined_embedding_list.append(embedding)
        combined_name_list.append(name)
    #print(combined_embedding_list)
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

from datetime import datetime

def get_low_attendance_students(section):
    # Get today's date in the same format as your attendance records


    first_today_str = datetime.now().strftime('%m-%d-%Y')
    today_str = first_today_str.replace("-", "_")
    #print("today_str",today_str)
    
    doc = get_doc('student_doc')
    #print(doc)
    if doc is None:
        print("No document found")
        return []

    students = doc['students'].get(section, {})
    low_attendance_students = []
    for student_id, student_data in students.items():
        #print("student_id",student_id)
        if student_id == 'class_photos':
            continue
        # Initialize counts for today
        total_sessions_today = 0
        attended_sessions_today = 0
        # Check if today's date is in the attendance records
        today_sessions = student_data['attendance'].get(today_str, {})
        #print("today_sessions",today_sessions)
        for _, attended in today_sessions.items():
            total_sessions_today += 1
            if attended:
                attended_sessions_today += 1
        
        # Calculate attendance rate for today
        attendance_rate_today = (attended_sessions_today / total_sessions_today) * 100 if total_sessions_today > 0 else 0
        
        # Print attendance info for debugging
        #print(f"Student ID: {student_id}, Attended Sessions Today: {attended_sessions_today}, Total Sessions Today: {total_sessions_today}, Attendance Rate Today: {attendance_rate_today}%")
        
        # Decide if the student has low attendance today
        if attendance_rate_today <= 50:###AATTENTION 50% is just a number I picked up AND IT IS A THRESHOLD
            #print(f"Student {student_id} has low attendance today ({attendance_rate_today}%)")
            low_attendance_students.append(student_id)
            print("low_attendance_students",low_attendance_students)
    names = retrieve_names_from_class(section)
    result = [name for name in names if name not in low_attendance_students]
    print(  "result",result)

    for name in result:
        update_overall_attendance(section, name, True, today_str)
        

    return low_attendance_students
section = 'CSC_4996_001_W_2024'
#get_low_attendance_students(section)
#names = retrieve_names_from_class(section)
# Assuming the get_doc function is defined and works as intended

def get_class_id(doc_id):
    # Retrieve the document from Firebase
    doc = get_doc(doc_id)
    
    if not doc or 'classes' not in doc:
        print("Document not found or does not contain 'classes'.")
        return [], [], [], [], []
    
    subjects, course_numbers, class_sections, terms, years = [], [], [], [], []
    # Mapping for term codes to their full names
    term_mapping = {"S": "Summer", "W": "Winter", "F": "Fall"}
    
    for class_id, details in doc['classes'].items():
        parts = class_id.split("_")
        if len(parts) == 5:
            subject, course_number, class_section, term_code, year = parts
            
            # Check for duplicates before appending
            if subject not in subjects:
                subjects.append(subject)
            if course_number not in course_numbers:
                course_numbers.append(course_number)
            if class_section not in class_sections:
                class_sections.append(class_section)
            term_full = term_mapping.get(term_code, "Invalid Term")
            if term_full not in terms:
                terms.append(term_full)
            if year not in years:
                years.append(year)
    
    return subjects, course_numbers, class_sections, terms, years


def get_name(names):
    doc = get_doc('user_doc')
    if doc is None:
        print("No document found")
        return []
    full_names = []
    for name in names:
        full_name = doc['users'][name]['fname'] + " " + doc['users'][name]['lname']
        full_names.append(full_name)
    print(full_names)
    return full_names
# To use the function, you would call it with your document ID
# Example usage:
#subjects, course_numbers, class_sections, terms, years = get_class_id('class_doc')

# Print the arrays to verify no duplicates
# print("Subjects:", subjects)
# print("Course Numbers:", course_numbers)
# print("Class Sections:", class_sections)
# print("Terms:", terms)
# print("Years:", years)


#low_attendance_students = get_low_attendance_students(section)
#print("Students with <= 10% attendance:", low_attendance_students)
#  ------------------------------  TESTING CODE  ------------------------------
print("---------------------- START DATABASE TESTING ----------------------")
# reset_docs()
# section='CSC_4996_001'

# reset_docs()
section = 'CSC_4996_001_W_2024'
# retrieve_class_embedding(section)
# retrieve_encodings_from_class('CSC_4996_001')
# combine_pt_files('CSC_4996_001')
# get_all_docs()

# update_doc(student_doc, 'students.CSC_4996_001.hc9082.attendance.02_08_2024.17_40_00', True)
# add_student('CSC_4996_001', 'hi6576')
# update_student_attendance('CSC_4996_001', 'hc9082', True, '02_08_2024', '17_40_00')
# update_student_attendance('CSC_4996_001', 'hc9082', True)
# update_student_photo('hc9082', 'photos/hc9082/hc9082.jpg')
# update_student_photo('hi4718', 'photos/hi4718/hi4718.jpg')
# update_class_photo(section, 'photos/hi6576/hi6576.jpg')
# remove_student_photo('hc9082')
# remove_student_photo('hc9082')

# add_student_to_class(section, 'hz2948')
# add_student('hz2948', 'John', 'Doe', 'student')
# add_student('hz2948', 'John', 'Doe', 'student')
# add_student_to_class(section, 'hz2948')
# add_student_to_class(section, 'hz2948')
# add_class('CSC_4996_001', 'mousavi')
# add_class('CSC_4996_004', 'mousavi')

# print(retrieve_file('hc9082', 'picture'))
# print(retrieve_names())
# retrieve_encodings_from_class('CSC_4996_001')

# update_photo_status(section, 'hc9082', "Accepted")
# update_photo_status_batch('hc9082', "Accepted")

print(retrieve_names_from_class(section))

print("---------------------- END DATABASE TESTING ----------------------")