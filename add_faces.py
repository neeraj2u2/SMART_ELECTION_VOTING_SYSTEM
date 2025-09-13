import cv2
import pickle
import numpy as np
import os
import tkinter as tk
from tkinter import messagebox
from PIL import Image, ImageTk

# Create data directory if needed
if not os.path.exists('data/'):
    os.makedirs('data/')

# Initialize face detector and camera
facedetect = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
video = cv2.VideoCapture(0)

# Global variables
faces_data = []
framesTotal = 51
captureAfterFrame = 2
name = ""
i = 0
imgtk = None  # Keep reference to prevent garbage collection

# Create main window
root = tk.Tk()
root.title("Add Face Data")
root.geometry("700x550")

# UI components
label = tk.Label(root, text="Enter Your Aadhar Number", font=("Arial", 14))
label.pack(pady=10)

entry = tk.Entry(root, font=("Arial", 14))
entry.pack(pady=5)

canvas = tk.Canvas(root, width=640, height=480)  # Adjusted to common webcam resolution
canvas.pack()

progress_label = tk.Label(root, text="0 / {} Faces Captured".format(framesTotal), font=("Arial", 12))
progress_label.pack(pady=5)

def update_frame():
    global i, faces_data, imgtk
    
    ret, frame = video.read()
    if not ret:
        root.after(10, update_frame)
        return
    
    frame = cv2.flip(frame, 1)  # Mirror for natural movement
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    faces = facedetect.detectMultiScale(gray, 1.3, 5)

    for (x, y, w, h) in faces:
        crop_img = frame[y:y+h, x:x+w]
        resized_img = cv2.resize(crop_img, (50, 50))
        if len(faces_data) <= framesTotal and i % captureAfterFrame == 0:
            faces_data.append(resized_img)
        i += 1
        cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)

    # Convert to RGB for Tkinter
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    img = Image.fromarray(rgb_frame)
    imgtk = ImageTk.PhotoImage(image=img)
    canvas.create_image(0, 0, anchor=tk.NW, image=imgtk)
    
    # Update progress
    progress_label.config(text=f"{len(faces_data)} / {framesTotal} Faces Captured")

    # Continue capturing until we have enough frames
    if len(faces_data) < framesTotal:
        root.after(10, update_frame)
    else:
        save_data()

def start_capture():
    global name, faces_data, i
    name = entry.get().strip()
    if not name:
        messagebox.showerror("Error", "Please enter your Aadhar number.")
        return
    faces_data = []
    i = 0
    update_frame()  # Start the video feed

def save_data():
    global name, faces_data
    if not faces_data:
        messagebox.showerror("Error", "No face data captured!")
        return
        
    faces_data_np = np.asarray(faces_data)
    faces_data_np = faces_data_np.reshape((len(faces_data), -1))  # Dynamic reshaping

    # Handle names
    if 'names.pkl' not in os.listdir('data/'):
        names = [name] * len(faces_data)
        with open('data/names.pkl', 'wb') as f:
            pickle.dump(names, f)
    else:
        with open('data/names.pkl', 'rb') as f:
            names = pickle.load(f)
        names += [name] * len(faces_data)
        with open('data/names.pkl', 'wb') as f:
            pickle.dump(names, f)

    # Handle face data
    if 'faces_data.pkl' not in os.listdir('data/'):
        with open('data/faces_data.pkl', 'wb') as f:
            pickle.dump(faces_data_np, f)
    else:
        with open('data/faces_data.pkl', 'rb') as f:
            faces = pickle.load(f)
        faces = np.append(faces, faces_data_np, axis=0)
        with open('data/faces_data.pkl', 'wb') as f:
            pickle.dump(faces, f)

    messagebox.showinfo("Success", "Face data successfully saved.")
    video.release()
    root.destroy()

# Start button
button = tk.Button(root, text="Start Face Capture", font=("Arial", 14), command=start_capture)
button.pack(pady=20)

root.mainloop()
