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


# Connect to firebase db
# cred_fp stores the filepath to the database credentials file, and assigns it as the credentials for the database.
cred_fp = str(Path.cwd()) + "\db_credentials.json"
cred = credentials.Certificate(cred_fp)
# Initialize the connection to the firebase database
firebase_admin.initialize_app(cred, {'storageBucket': 'facecheck-93450.appspot.com'})

#  Assign the firebase database to a variable db
db = firestore.client()
# Name of the Firebase collection which stores all the docs
collectionName = "infoCollection"
# Variables storing each doc name used in this code
class_doc = "class_doc"
student_doc = "student_doc"
user_doc = "user_doc"


#  ------------------------------  MAIN FUNCTIONALITY  ------------------------------
#  Reset all documents in Firebase with prepopulated information
def reset_docs():
    # Dictionary for class data. Includes two default classes in different semesters.
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
    # Dictionary for student data. Includes two default classes in different semesters and three enrolled students.
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
    # Dictionary for user data. Includes three default students and a professor user.
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

    # Delete all documents in the database using a reference to the collection so that all docs can be recreated
    doc_ref = db.collection(collectionName)
    doc_ref.document(class_doc).delete()
    doc_ref.document(student_doc).delete()
    doc_ref.document(user_doc).delete()
    # Recreate all docs using the previous prepopulated data
    doc_ref.document(class_doc).set(dataClass)
    doc_ref.document(student_doc).set(dataStudent)
    doc_ref.document(user_doc).set(dataUser)
    
    # Upload photos for all students so that the model works with several faces
    update_student_photo('hc9082', 'photos/hc9082/hc9082.jpg')
    update_student_photo('hi4718', 'photos/hi4718/hi4718.jpg')
    update_student_photo('hi6576', 'photos/hi6576/hi6576.jpg')
    # Set encoding status to true so that the desktop application will force a new class embedding file to be generated
    update_class_encoding_status('CSC_4996_001_W_2024', True)
    update_class_encoding_status('CSC_4500_002_S_2024', True)
    # Add an extra student to the database, with no photo or class enrollments
    add_student('hz2948', 'John', 'Doe', 'student')

    # Print the ID of each document as a debug message
    print("Document ID: ", doc_ref.id)
    

#  Retrieve all docs in collection
def get_all_docs():
    # Retrieve all documents
    docs = (
        db.collection(collectionName)
        .stream()
    )
    
    # Iterate over documents and store their IDs and data into a list of dictionary objects
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

#  Retrieve a single document from database and return as a dictionary
def get_doc(doc_id):
    # Assign a reference to the document and get its contents
    doc_ref = db.collection(collectionName).document(doc_id)
    doc = doc_ref.get()
    # Return as a dicionary
    if doc.exists:
        return doc.to_dict()
    else:
        print(f"Document {doc_id} not found in {collectionName}.")
        return None
    
    
#  Recursively search dictionary. 
#  "key" represents a key to search for in the dictionary, "data" is the data being searched for the key
def lookup(key, data):
    if key in data:
        return data[key]
    for value in data.values():
        # Is the object a dictionary?
        if isinstance(value, dict):
            # Successfully found item, return the value/definition associated with that key
            return lookup(key, value)
    # Could not find the key in data
    return None


#  Get current date and time
def getDate():
    # Get the date right now
    now = datetime.now()
    return now.strftime("%m_%d_%Y")

def getTime():
    # Get the time right now
    now = datetime.now()
    return now.strftime("%H_%M_%S")
    
       
#  Update existing document
def update_doc(doc_id, key, value):
    # Get a reference to the specified document
    doc_ref = db.collection(collectionName).document(doc_id)
    # Update the document with the given key & value dictionary pair
    doc_ref.update({
        key: value
    })

#  Add new class section
def add_class(section, prof):
    # Get the class document from Firebase as a dictionary object
    class_dict = get_doc(class_doc)
    
    # If the class ID is found in the class, fail to add it since it already exists. Otherwise add it
    if lookup(section, class_dict) != None:
        print("Error: Cannot add class '" + section + "' because the class already exists.")
    else:
        # Update the doc using the path as the dictionary key, and prof as the dictionary value
        key = 'classes.' + section + '.professor'
        update_doc(class_doc, key, prof)
        print("Class '" + section + "' successfully added.")
    
#  Add new student to **DATABASE**
def add_student(accessid, fname, lname, role):
    # Get the user document from Firebase as a dictionary object
    user_dict = get_doc(user_doc)
    
    # If the user already exists, fail to add. Otherwise add successfully.
    if lookup(accessid, user_dict) != None:
        print("Error: Cannot add user '" + accessid + "' because the user already exists.")
    else:
        # Assign the user a default first name, last name, picture, encoding, role, and audit log entry
        # key and value represent key/value pairs in a dictionary object to be added to the User doc in Firebase
        # Update the doc with the key/value pair after they are assigned
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
        
        # Debug message
        print("Student '" + accessid + "' successfully added.")
        
#  Add new student to **CLASS**
#  Section represents the class section/class ID
def add_student_to_class(section, accessid):
    # Save data from the student doc and user doc in Firebase as dictionary objects
    student_dict = get_doc(student_doc)
    user_dict = get_doc(user_doc)
    
    # Does the student already exist in this class?
    if lookup(accessid, student_dict['students'][section]) != None:
        print("Error: Cannot add user '" + accessid + "' because the user is already in " + section + ".")
    # Does the student exist at all?
    elif lookup(accessid, user_dict) == None:
        print("Error: Cannot add user '" + accessid + "' because the user does not exist.")
    # If above conditions are not the case, add the student to the class
    else:
        # Use dictionary key/value pairs to update the student and class documents with necessary information.
        # Initialize the attendance field for the student in Firebase by entering a zero date which will never be used.
        # This will make sure that the attendance path DOES exist in Firebase when checked for later.
        key = 'students.' + section + '.' + accessid + '.attendance.00_00_0000.00_00_00'
        update_doc(student_doc, key, True)
        # Force an update to the class encoding status so that a new encoding file is generated.
        classKey = 'classes.' + section + '.encoding_update'
        update_doc(class_doc, classKey, True)
        
        # Debug confirmation message
        print("Student '" + accessid + "' successfully added to " + section + ".")
   
    
#  ------------------------------  SHORTCUT FUNCTIONS  ------------------------------
#  Get class name from class id
def get_class_name(section):
    # Get the class document's contents from Firebase as a dictionary object, and return the class's name
    # from the class's information.
    class_dict = get_doc(class_doc)
    return class_dict['classes'][section]['class_name']

#  Update student attendance
#  "section" represents the class section/class ID. "value" represents the attendance value (true/false)
#  If no date/time are entered by default, they are assigned to current time
def update_student_attendance(section, name, value, date = getDate(), time = getTime()):
    # Get the contents of the student doc in Firebase as a dictionary object.
    student_dict = get_doc(student_doc)
    
    # Does the user exist in this class? If so, update the attendance document with the appropriate dictionary 
    # key/value pair representing the student's attendance at that current date/time.
    if lookup(name, student_dict['students'][section]) == None:
        print("Error: Cannot update attendance for '" + name + "' because the user does not exist.")
    else:
        key = 'students.' + section + '.' + name + '.attendance.' + date + '.' + time
        update_doc(student_doc, key, value)
        print("Student '" + name + " marked as " + str(value) + " on " + date + " at " + time + ".")

#  Update a student's overall attendance for the day
#  "section" represents the class section/class ID. "value" represents the attendance value (true/false)
#  If no date ise entered by default, they are assigned to current date
def update_overall_attendance(section, name, value, date = getDate()):
    # Get the contents of the student doc in Firebase as a dictionary object.
    student_dict = get_doc(student_doc)
    
    # Does the user exist for this class? If so, update the attendance document with the appropriate dictionary 
    # key/value pair representing the student's attendance for the current date.
    if lookup(name, student_dict['students'][section]) == None:
        print("Error: Cannot update overall attendance for '" + name + "' because the user does not exist.")
    else:
        key = 'students.' + section + '.' + name + '.attendance.' + date + '.Overall'
        update_doc(student_doc, key, value)
        print("Student '" + name + " marked as " + str(value) + " OVERALL on " + date + ".")

#  Update student photo 
def update_student_photo(name, file):
    # Create a new Firebase Storage bucket
    bucket = storage.bucket()
    # Set a name for the blob that will be used to upload the photo
    imageBlob = bucket.blob(name + "_photo")
    # Store the user's name as a list, used for make_pt_file
    name_list = [name]
    
    # Crop student photo & upload encoding
    cropped_image = detect_and_crop_face(file)
    # Verify that an image was returned successfully before uploading
    if cropped_image is not None:
        # Save cropped photo to temporary location and upload
        with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as temp_file:
            cv2.imwrite(temp_file.name, cropped_image)
            imageBlob.upload_from_filename(temp_file.name)
        # Make the image blob public so that the URL is accessible
        imageBlob.make_public()
            
        # Save encoding to temporary location and upload
        embedding_link = make_pt_file(face_encode(cropped_image,device=torch.device('cuda' if torch.cuda.is_available() else 'cpu')), name_list)
        
        # Upload photo and encoding using dictionary key/value pairs
        userPhotoKey = 'users.' + name + '.picture'
        update_doc(user_doc, userPhotoKey, imageBlob.public_url)
        userEncodingKey = 'users.' + name + '.encoding'
        update_doc(user_doc, userEncodingKey, embedding_link)
        print("Face uploaded.")
    else:
        print("Error: No face detected, or there was an error processing the image.")


#  Update class photo
#  Section represents the class section/class ID. date and time are assigned to current time if not given
def update_class_photo(section, frame, date = getDate(), time = getTime()):
    # Create a new Firebase Storage bucket
    bucket = storage.bucket()
    # Set a name for the blob that will be used to upload the photo
    imageBlob = bucket.blob(section + "/" + date + "/" + time + "_photo")
    
    # Save cropped photo to temporary location and upload
    with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as temp_file:
        cv2.imwrite(temp_file.name, frame)
        imageBlob.upload_from_filename(temp_file.name)
    # Make the image blob public so that the URL is accessible
    imageBlob.make_public()
        
    # Upload photo and encoding using dictionary key/value pairs     
    key = 'students.' + section + '.class_photos.' + date + '.' + time
    update_doc(student_doc, key, imageBlob.public_url)
    print("Class photo uploaded for" + date + " at " + time + ".")


# Update photo status for professor to approve     
# Arguments are class section/class ID, student name, and the desired value for the student's photo status   
def update_photo_status(section, name, value):
    # Store the contents of the user and student documents in Firebase as dictionary objects
    user_dict = get_doc(user_doc)
    student_dict = get_doc(student_doc)
    
    # Does this user exist?
    if lookup(name, user_dict) == None:
        print("Error: Cannot update photo status for '" + name + "' because the user does not exist.")
    # Is this user part of this class?
    elif lookup(name, student_dict['students'][section]) == None:
        print("Error: Cannot update photo status for '" + name + "' because the user is not in class '" + section + "'.")
    # If the above conditions are not the case, use dictionary key/value pairs to update the student's photo status to the given value
    else:
        key = 'students.' + section + '.' + name + '.picture_status'
        print("Updated photo status for '" + name + "' in class '" + section + "'.")
        update_doc(student_doc, key, value)

# Update photo status for professor to approve (AS A BATCH)   
# Arguments are student name, and the desired value for the student's photo status   
def update_photo_status_batch(name, value):
    # Store the contents of the user and student documents in Firebase as dictionary objects
    user_dict = get_doc(user_doc)
    student_dict = get_doc(student_doc)
    
    # Does this user exist?
    if lookup(name, user_dict) == None:
        print("Error: Cannot update photo status for '" + name + "' because the user does not exist.")
    # If the user exists, iterate through all class sections/class IDs the user is in and update the photo status to the given value.
    else:
        for section in student_dict['students']:
            # Checks if a user is part of that class
            if lookup(name, student_dict['students'][section]) == None:
                print("Error: Cannot update photo status for '" + name + "' because the user is not in class '" + section + "'.")
            else:
                # Update the student attendance document using dictionary key/value pairs
                key = 'students.' + section + '.' + name + '.picture_status'
                print("Updated photo status for '" + name + "' in class '" + section + "'.")
                update_doc(student_doc, key, value)
    

#  Remove student photo
def remove_student_photo(name):
    # Get the Firebase Storage bucket and blob in which the student's photo is saved in
    bucket = storage.bucket()
    blob = bucket.blob(name + "_photo")
    # If the image blob exists, delete it
    if blob.exists():
        blob.delete()

        # Remove photo and encoding by updating the respective dictionary key/value pairs. Update the user doc with these changes.
        userKey = 'users.' + name + '.picture'
        update_doc(user_doc, userKey, "NO PHOTO")
        userKey = 'users.' + name + '.encoding'
        update_doc(user_doc, userKey, "NO ENCODING")
        print("Photo for '" + name + "' deleted successfully.")
    else:
        print("Error: Student '" + name + "', if they exist, has no photo in the database.")


# Retrieve file from Firebase storage (filetype is 'picture' or 'encoding')
def retrieve_file(name, filetype): 
    # Get the user doc from Firebase as a dictionary object
    doc = get_doc(user_doc)

    # Debug message if there is no file for the given filetype
    if (doc['users'][name][filetype] == 'NO ENCODING'):
        print("Error: Cannot retrieve filetype '" + filetype + "' for user '" + name + "'.")
    else:
        print("Retrieved filetype '" + filetype + "' for user '" + name + "'.")
        
    # Return link to the file
    return doc['users'][name][filetype]

# Retrieve class embedding file from Firebase storage
def retrieve_class_embedding(section): 
    # Get the user doc from Firebase as a dictionary object
    doc = get_doc(class_doc)

    # Debug message if there is no class encoding/embedding file
    if (doc['classes'][section]['class_encoding'] == 'NO ENCODING'):
        print("Error: Cannot retrieve filetype class encoding for class '" + section + "'.")
    else:
        print("Retrieved class encoding for class '" + section + "'.")
    print(doc['classes'][section]['class_encoding'])
    # Return link to the encoding/embedding file
    return doc['classes'][section]['class_encoding']


# Retrieve array of names for all students with approved photos in a class section
def retrieve_approved_names_from_class(section): 
    # Get the student attendance doc from Firebase as a dictionary object
    doc = get_doc(student_doc)    
    # Get a list of names for that class section/class ID
    names = list(doc['students'][section].keys()) 
    
    # Remove class_photos from names since it is not an actual student
    if "class_photos" in names:
        names.remove("class_photos")
     
    # Remove students who do not have an approved photo
    final_name_list = []
    for name in names:
        if doc['students'][section][name]['picture_status'] == "Accepted":
            final_name_list.append(name)
        
    # Return the resulting list of students
    return final_name_list

# Retrieve array of names for all students in a class section
def retrieve_names_from_class(section): 
    # Get the student attendance doc from Firebase as a dictionary object
    doc = get_doc(student_doc)    
    # Get a list of names for that class section/class ID
    names = list(doc['students'][section].keys()) 
    
    # Remove class_photos from names since it is not an actual student
    if "class_photos" in names:
        names.remove("class_photos")
        
    return names
    
import numpy as np 
# Retrieve all encodings for a class section
def retrieve_encodings_from_class(section):
    # Get the list of names from the class with an approved photo
    names = retrieve_approved_names_from_class(section)    
    
    # For each name, get the list of encoding files from each student with approved photos.
    # If the student has no encoding, skip them.
    encoding_list = []
    for name in names:
        retrieved_encoding = retrieve_file(name, 'encoding')
        if retrieved_encoding != 'NO ENCODING':
            encoding_list.append(retrieved_encoding)
    
    # Return the resulting list of encodings
    return encoding_list 

# The following function was written by Ahmed Minhaj
# Download the emedding/pt file for the student
def download_pt_file_student(url):
    # Get the response for the URL containing the link to the file
    response = requests.get(url)
    response.raise_for_status()
    # Create a buffer and get the name & embedding
    buffer = BytesIO(response.content)
    embedding, name = torch.load(buffer, map_location='cpu')
    return embedding[0], name[0]

#  Update class encoding
#  Arguments are class section/class ID and a given class encoding/embedding file
def update_class_encoding(section, file):
    # Store the contents of the class document in Firebase as a dictionary object
    doc = get_doc(class_doc)
    
    # If the flag to update the class's encoding is set to true, upload the file
    if doc['classes'][section]['class_encoding_update'] == True:
        # Create a Firebase storage bucket and make a blob to store the file within it
        bucket = storage.bucket()
        blob = bucket.blob(section + ".pt")
        blob.upload_from_filename(file)
        # Make the blob public so that the URL is accessible
        blob.make_public()
        # Update encoding status to show encoding update is no longer needed
        update_class_encoding_status(section, False)

        # Update the class document with the link to the file using a dictionary key/value pair
        key = 'classes.' + section + '.class_encoding'
        update_doc(class_doc, key, blob.public_url)
    else:
        print("Error: Encoding update is not needed for '" + section + "'.")

# Set flag that class encoding needs update
def update_class_encoding_status(section, value):
    key = 'classes.' + section + '.class_encoding_update'
    update_doc(class_doc, key, value)

# This function was written by Ahmed Minhaj
# Combine all the pt/encoding/embedding files of the students in the class and make a class pt file, then save it as the class name
# section represents the class section/class ID
def combine_pt_files(section):
    # Arrays for the lists of combined embeddings and names
    combined_embedding_list = []
    combined_name_list = []
    # Retrieve all encoding URLS for the class
    urls = retrieve_encodings_from_class(section)
 
    for url in urls:
        # get the embedding and name from the url
        embedding, name = download_pt_file_student(url)
        # append the embedding and name to the list
        combined_embedding_list.append(embedding)
        combined_name_list.append(name)
    # save the combined embedding and name list as a pt file
    torch.save([combined_embedding_list,combined_name_list], f'{section}.pt')
    # upload the file to the firebase using section as the dict key and the pt file name as the dict value
    update_class_encoding(section, f'{section}.pt')

# This function was written by Ahmed Minhaj
# Download the file from the url and save it as the section name
def download_file_combine(url, section):
    # Download the file from the URL
    #credit: https://stackoverflow.com/questions/16694907/download-large-file-in-python-with-requests
    with requests.get(url, stream=True) as response:
        # Open the contents and write the chunks into a file
        response.raise_for_status()
        with open(section, 'wb') as file:
            for chunk in response.iter_content(chunk_size=8192):
                file.write(chunk)
    
    print(f"File downloaded and saved as {section}")

# This function was written by Ahmed Minhaj
# Return the low attendance students (students who were present for less than 50% of timestamps)
def get_low_attendance_students(section):
    # Get today's date in the same format as the attendance records
    first_today_str = datetime.now().strftime('%m-%d-%Y')
    # Convert the date to the format used in the attendance records
    today_str = first_today_str.replace("-", "_")

    # Retrieve the document from Firebase
    doc = get_doc('student_doc')
    if doc is None:
        print("No document found")
        return []

    # Get the students for the specified section
    students = doc['students'].get(section, {})
    low_attendance_students = []
    for student_id, student_data in students.items():
        # Skip the class_photos key
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
        
        # Decide if the student has low attendance today
        if attendance_rate_today <= 50:   ###AATTENTION 50% is just a number I picked up AND IT IS A THRESHOLD
            low_attendance_students.append(student_id)

    #list of all students for the section
    names = retrieve_names_from_class(section)
    # Remove low attendance students from the list of all students
    
    high_attendance = [name for name in names if name not in low_attendance_students]

    # Update overall attendance for high attendance students as True
    for name in high_attendance:
        update_overall_attendance(section, name, True, today_str)
        
    # Return the list of low attendance students
    return low_attendance_students

# This function was written by Ahmed Minhaj
# Get the class id and returns the subjects, course numbers, class sections, terms, 
# and years so that we can use it as a dropdown menu
def get_class_id(doc_id):
    # Retrieve the document from Firebase as a dictionary object
    doc = get_doc(doc_id)
    # error handling
    if not doc or 'classes' not in doc:
        print("Document not found or does not contain 'classes'.")
        return [], [], [], [], []
    # Initialize lists to store unique values
    subjects, course_numbers, class_sections, terms, years = [], [], [], [], []
    # Mapping for term codes to their full names
    term_mapping = {"S": "Summer", "W": "Winter", "F": "Fall"}
    
    # Iterate over each class in the document
    for class_id, details in doc['classes'].items():
        parts = class_id.split("_")
        # Check if the class ID is in the correct format
        if len(parts) == 5:
            subject, course_number, class_section, term_code, year = parts
            
            # Check for duplicates before appending so that we only store unique values
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

# This function was written by Ahmed Minhaj
# Return the full names of the students
def get_name(names):
    # Get the contents of the user document in Firebase as a dictionary object
    doc = get_doc('user_doc')
    if doc is None:
        print("No document found")
        return []
    # Get the full names of each student
    full_names = []
    for name in names:
        full_name = doc['users'][name]['fname'] + " " + doc['users'][name]['lname']
        full_names.append(full_name)
    print(full_names)
    return full_names


#  ------------------------------  TESTING CODE  ------------------------------
# This section was previously used for testing any functions in this file
# print("--------------------- DATABASE.PY STARTED ---------------------")
# reset_docs()
# print("---------------------- DATABASE.PY ENDED ----------------------")