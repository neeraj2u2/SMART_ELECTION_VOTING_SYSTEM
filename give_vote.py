# ======================== givevote.py ===========================

import cv2
import pickle
import numpy as np
import os
import csv
import time
from datetime import datetime
from win32com.client import Dispatch
from sklearn.neighbors import KNeighborsClassifier

# Function to speak via voice (Windows only)
def speak(text):
    speaker = Dispatch("SAPI.SpVoice")
    speaker.Speak(text)

# Ensure data directory exists
if not os.path.exists('data/'):
    os.makedirs('data/')

# Load face labels and data
with open('data/names.pkl', 'rb') as f:
    LABELS = pickle.load(f)
with open('data/faces_data.pkl', 'rb') as f:
    FACES = pickle.load(f)

# Train KNN classifier
knn = KNeighborsClassifier(n_neighbors=5)
knn.fit(FACES, LABELS)

# Load background UI
imgBackground = cv2.imread("background.png")
if imgBackground is None:
    imgBackground = 255 * np.ones((720, 1280, 3), dtype=np.uint8)
else:
    imgBackground = cv2.resize(imgBackground, (1280, 720))

# Draw voting options
cv2.putText(imgBackground, "Press 1 for BJP", (750, 100), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 0, 255), 3)
cv2.putText(imgBackground, "Press 2 for CONGRESS", (750, 160), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (255, 0, 0), 3)
cv2.putText(imgBackground, "Press 3 for AAP", (750, 220), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 255, 0), 3)
cv2.putText(imgBackground, "Press 4 for NOTA", (750, 280), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 0, 0), 3)

# Check for duplicate vote
def check_if_exists(value):
    try:
        with open("Votes.csv", "r") as csvfile:
            reader = csv.reader(csvfile)
            for row in reader:
                if row and row[0] == value:
                    return True
    except FileNotFoundError:
        return False
    return False

# Start video
video = cv2.VideoCapture(0)
video.set(3, 1280)
video.set(4, 720)

facedetect = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
COL_NAMES = ['NAME', 'VOTE', 'DATE', 'TIME']

output = None

while True:
    ret, frame = video.read()
    if not ret:
        continue
    frame = cv2.resize(frame, (640, 480))
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    faces = facedetect.detectMultiScale(gray, 1.3, 5)

    output = None
    for (x, y, w, h) in faces:
        crop_img = frame[y:y+h, x:x+w]
        resized_img = cv2.resize(crop_img, (50, 50)).flatten().reshape(1, -1)
        output = knn.predict(resized_img)
        ts = time.time()
        date = datetime.fromtimestamp(ts).strftime("%d-%m-%Y")
        timestamp = datetime.fromtimestamp(ts).strftime("%H:%M-%S")
        exist = os.path.isfile("Votes.csv")

        # Show face box
        cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
        cv2.rectangle(frame, (x, y-40), (x+w, y), (0, 255, 0), -1)
        cv2.putText(frame, str(output[0]), (x, y-15), cv2.FONT_HERSHEY_COMPLEX, 1, (255, 255, 255), 1)

    # Display frame on left of background
    imgBackground[120:120+480, 50:50+640] = frame
    cv2.imshow("Smart Voting System", imgBackground)
    k = cv2.waitKey(1)

    if output is not None:
        if check_if_exists(str(output[0])):
            speak("YOU HAVE ALREADY VOTED")
            time.sleep(2)
            break

        vote = ""
        if k == ord('1'):
            vote = "BJP"
        elif k == ord('2'):
            vote = "CONGRESS"
        elif k == ord('3'):
            vote = "AAP"
        elif k == ord('4'):
            vote = "NOTA"

        if vote:
            speak("YOUR VOTE HAS BEEN RECORDED")
            time.sleep(1)
            with open("Votes.csv", "a", newline='') as csvfile:
                writer = csv.writer(csvfile)
                if not exist:
                    writer.writerow(COL_NAMES)
                attendance = [str(output[0]), vote, date, timestamp]
                writer.writerow(attendance)
            speak("THANK YOU FOR PARTICIPATING IN THE ELECTIONS")
            time.sleep(2)
            break

video.release()
cv2.destroyAllWindows()
