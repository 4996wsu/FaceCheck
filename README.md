# FaceCheck

![image](https://github.com/FaceCheckOrg/FaceCheck/assets/74390236/3f669273-06ed-41ac-9e6c-8cd39db46af0)


# Table of Contents


  - [Overview](#overview)
  - [Contributors](#contributors)
  - [Software Requirements Specification](https://waynestateprod-my.sharepoint.com/:w:/g/personal/hi6576_wayne_edu/Efd8_T9tG8lDq7v1Ug7txSwB3wWseoMIsl8G_XZdJ54nXA?e=NuUeow)
  - [Installation](#installation)
  - [Firebase Configuration](#firebase-Configuration)
  - [Credentials you need](#credentials-you-need)
  - [Technology Stack](#technology-stack)



# Overview

We're excited to unveil FaceCheck, our innovative solution that leverages face recognition technology to revolutionize the way attendance is recorded and managed in educational settings. Designed specifically with both students and educators in mind, FaceCheck automates the attendance process, ensuring both accuracy and efficiency.

Here’s the lowdown: Traditional methods of taking attendance can be slow and prone to errors. FaceCheck streamlines this by utilizing advanced face recognition technology to automatically record attendance every three minutes during class. This not only reduces errors but also significantly cuts down the time spent on manual checks.

For students, getting started is a breeze. Through our web application, you can quickly enroll in the system by uploading a photo of yourself. It’s simple, fast, and secure, setting you up to be recognized by our system in no time.

Teachers, on the other hand, will find FaceCheck to be a vital tool in classroom management. Our desktop application kicks off the automated attendance process effortlessly, while our web interface allows you to manage class rosters and delve into detailed attendance data. This access to real-time information and historical attendance trends enables more informed decisions and better student engagement.

What we’re delivering here isn’t just automation—it’s a smarter, data-driven approach to managing attendance that saves time and enhances the educational experience. FaceCheck empowers you to focus on what matters: teaching and learning.

We’re thrilled to see how FaceCheck will transform classroom dynamics and make educational administration smoother and more productive. Stay tuned for further updates, and thank you for exploring FaceCheck with us!


# Contributors
1. Ahmed Minhaj<br />
   Email: ahmed.minhaj@wayne.edu
2. Aafnan Mahmood<br />
   Email: aafnan@wayne.edu
3. Mohamad Hachem<br />
   Email: hi6576@wayne.edu
# Installation
This guide provides detailed instructions on setting up and running the application on your local machine. Please follow the steps below carefully to ensure proper setup.

## Project Configuration
Ensure you have Python 3.10.4 installed on your system. If you do not have Python installed, you can download it from the [official Python website](https://www.python.org/downloads/).

### Step 1: Clone the Repository
First, you need to clone the project repository.
```bash
cd path-to-your-project
```
```bash
git clone https://github.com/FaceCheckOrg/FaceCheck.git
```
### Step 2: Set Up a Virtual Environment
To avoid conflicts we need to separate the environment. You can run this to make a new environment.
```bash
python -m venv venv
```
### Step 3: Activate the virtual environment:
```bash
.\venv\Scripts\activate
```
### Step 4: Install Dependencies: 
All our libraries and packages have been listed in the requirement.txt.
```bash
pip install -r requirements.txt
```
# Firebase Configuration 
For all aspects of FaceCheck to function, the database must first be set up on Firebase. The following instructions describe how to set up a Firestore database and Firebase storage to work with FaceCheck, along with setting some initial data for the desktop and web applications to use.

1. Create a Firebase account at https://firebase.google.com/ and create a new project. Keep all other options in the project’s creation unchanged.
2. Under Project Shortcuts, open Extensions. Open Firestore Database and Storage so that both are docked on the left-hand side of the page.
3. Create a new database with the location set to nam5 (United States). Start the database in production mode.
4. Start a new collection with the Collection ID of “infoCollection”. Enter “professor_doc” for the Document ID when prompted.
5. Add a field “professors” as an array. Enter any usernames within the array that you want to be reserved for professors. This will automatically assign the “professor” role to users who sign up with any of these usernames.
6. Under the “Rules” tab, replace your rules with the following, or adjust them to your liking:

    ```
    rules_version = '2';
    
    service cloud.firestore {
      match /databases/{database}/documents {
        match /{document=**} {
          allow read, write: if true;
        }
      }
    }
    ```

7. Open the Storage tab on the left-hand side of the page from Step 2 and set up Storage in production mode. Create the bucket.
8. Under the “Rules” tab, replace your rules with the following, or adjust them to your liking:

    ```
    rules_version = '2';
    
    service firebase.storage {
      match /b/{bucket}/o {
        match /{allPaths=**} {
          allow read, write: if true;
        }
      }
    }
    ```
    
9. On the left-hand side of the page, click the gear icon next to Project Overview, and click on Project Settings. Open the Service Accounts tab and click the radio button that says “Python”. Click “Generate new private key” and save the credentials file. Open this file and copy the contents.
10. Navigate to the FaceCheck directory and open the ai_model directory. Open db_credentials.json and paste the contents of the credentials file. Repeat this step in the db_credentials.json file stored in the FaceCheck/webapp directory.
11. In both the ai_model and webapp directories there should be files named database.py. Open both files.
12. Return to the Firebase Console and open the General tab of the project settings. Copy the Project ID and paste it into both database.py files at line 24, replacing the portion reading “facecheck-93450”.
13. In the Firebase Console, navigate to the bottom of the page to the “Your apps” section. Create a new web app by clicking the third icon from the left, labeled as “</>”.
14. Give the web app a nickname of your choosing. Hosting the website is not required for the application to function.
15. When prompted to add the Firebase SDK, ensure that “npm” is selected. Copy all the credentials within the contents of the “firebaseConfig” variable.
16. Open the FaceCheck/webapp/main/templates/main directory. Open base.html, enrollment.html, home.html, manageclass.html, and stats.html. Navigate to the script module in the code and find the “firebaseConfig” variable. Replace the contents of this variable with the contents of firebaseConfig viewed in the Firebase Console. Repeat this for each html file.
17. Open FaceCheck/ai_mode/database.py again and find the function “reset_docs()”. Execute this function through code to populate the database with a set of default users, classes, and attendance statistics.


## Running the Web Application:
```bash
cd webapp
```
If you are running it for the first time, please run this migrate command. 
```bash
python manage.py migrate
```
and to run the web application, use this command line 
```bash
python manage.py runserver
```
use this URL to view the web application.
```bash
http://127.0.0.1:8000/
```
## Running the Desktop Application:
```bash
cd ai_model
```
```bash
python desktop.py
```

# Credentials you need
## Student Account:
1. Username: hi4718<br/>
Password: sUdEN4um5mNPqh8<br/>
2. Username: hc9082<br/>
Password: waynestateuniversity <br/>
3. Username: hi6576<br/>
Password: sUdEN4um5mNPqh8<br/>
## Professor Account:
1. Username: dx6565<br/>
Password: Password <br/>



# Technology Stack

The technology stack for this mobile application involves both front-end and back-end development.

- **Front-end:** HTML, CSS -> Framework: Flowbite
- **Web Application Back-end:** Python -> Framework: Django
- **Desktop Application Back-end:** Python -> Framework: Tkinter
- **Database:** NOSQL -> Host: Firebase



