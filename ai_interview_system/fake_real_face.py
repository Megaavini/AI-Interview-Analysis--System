from tensorflow.keras.preprocessing.image import img_to_array
from keras.models import load_model
from collections import deque
import numpy as np
import cv2

print("Loading model...")

face_detector = cv2.CascadeClassifier("haarcascade_frontalface_default.xml")
model = load_model("liveness.model")

labels = ["Real", "Fake"]
colors = [(0,255,0),(0,0,255)]

# Average predictions over last 15 frames
prediction_history = deque(maxlen=15)

CONFIDENCE_THRESHOLD = 0.80

print("Starting camera...")

cap = cv2.VideoCapture(0)

while True:

    ret, frame = cap.read()

    if not ret:
        break

    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    faces = face_detector.detectMultiScale(
        gray,
        scaleFactor=1.3,
        minNeighbors=5,
        minSize=(80,80)
    )

    for (x,y,w,h) in faces:

        face = frame[y:y+h, x:x+w]

        face = cv2.resize(face,(32,32))

        face = face.astype("float32") / 255.0

        face = img_to_array(face)

        face = np.expand_dims(face,axis=0)

        preds = model.predict(face, verbose=0)[0]

        prediction_history.append(preds)

        avg_preds = np.mean(prediction_history, axis=0)

        confidence = np.max(avg_preds)

        if confidence < CONFIDENCE_THRESHOLD:
            label = "Checking..."
            color = (255,255,0)
        else:
            idx = np.argmax(avg_preds)
            label = f"{labels[idx]} {confidence*100:.1f}%"
            color = colors[idx]

        cv2.rectangle(frame,(x,y),(x+w,y+h),color,2)

        cv2.putText(frame,
                    label,
                    (x,y-10),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.7,
                    color,
                    2)

    cv2.imshow("Liveness Detection",frame)

    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

cap.release()

cv2.destroyAllWindows()