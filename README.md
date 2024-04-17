# FaceCheck

![image](https://github.com/FaceCheckOrg/FaceCheck/assets/74390236/3f669273-06ed-41ac-9e6c-8cd39db46af0)


# Table of Contents


  - [Overview](#overview)
  - [Contributors](#contributors)
  - [Software Requirements Specification](https://waynestateprod-my.sharepoint.com/:w:/g/personal/hi6576_wayne_edu/Efd8_T9tG8lDq7v1Ug7txSwB3wWseoMIsl8G_XZdJ54nXA?e=NuUeow)
  - [Installation](#installation)
  - [Credentials you need](#credentials-you-need)
  - [Technology Stack](#technology-stack)


# Overview

We're excited to unveil FaceCheck, our innovative solution that leverages face recognition technology to revolutionize the way attendance is recorded and managed in educational settings. Designed specifically with both students and educators in mind, FaceCheck automates the attendance process, ensuring both accuracy and efficiency.

Here’s the lowdown: Traditional methods of taking attendance can be slow and prone to errors. FaceCheck streamlines this by utilizing advanced face recognition technology to automatically record attendance every three minutes during class. This not only reduces errors but also significantly cuts down the time spent on manual checks.

For students, getting started is a breeze. Through our web application, you can quickly enroll in the system by uploading a photo of yourself. It’s simple, fast, and secure, setting you up to be recognized by our system in no time.

Teachers, on the other hand, will find FaceCheck to be a vital tool in classroom management. Our desktop application kicks off the automated attendance process effortlessly, while our web interface allows you to manage class rosters and delve into detailed attendance data. This access to real-time information and historical attendance trends enables more informed decisions and better student engagement.

What we’re delivering here isn’t just automation—it’s a smarter, data-driven approach to manage attendance that saves time and enhances the educational experience. FaceCheck empowers you to focus on what matters: teaching and learning.

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
## Firebase Configuration 
Please check the User Manual Second Section( Setting Up the database)

## Running the Web Application:
```bash
cd webapp
```
```bash
python manage.py migrate
```
```bash
python manage.py runserver
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
2 Username: hc9082<br/>
Password: waynestateuniversity <br/>
3. Username: hi6576<br/>
Password: <br/>
## Professor Account:
1. Username: dx6565<br/>
Password: Password <br/>



# Technology Stack

The technology stack for this mobile application involves both front-end and back-end development.

- **Front-end:** HTML, CSS -> Framework: Flowbite
  
- **Back-end:** Python -> Framework: Django
  
- **Database:** NOSQL Host: Firebase


## Future Potential



