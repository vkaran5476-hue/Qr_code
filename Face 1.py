import cv2
import os
from datetime import datetime
import winsound  # Windows only — replace with 'playsound' or 'pygame' on Mac/Linux

# ─── Paths ───────────────────────────────────────────────────────────────────
BASE = r"C:\Users\karan\PycharmProjects\PythonProject2\.venv\Lib\site-packages\cv2\data"
FACE_XML  = os.path.join(BASE, "haarcascade_frontalface_default.xml")
EYE_XML   = os.path.join(BASE, "haarcascade_eye.xml")
SMILE_XML = os.path.join(BASE, "haarcascade_smile.xml")

SAVE_DIR = "detected_faces"
os.makedirs(SAVE_DIR, exist_ok=True)

# ─── Load Cascades ────────────────────────────────────────────────────────────
face_cap  = cv2.CascadeClassifier(FACE_XML)
eye_cap   = cv2.CascadeClassifier(EYE_XML)
smile_cap = cv2.CascadeClassifier(SMILE_XML)

# ─── Settings ─────────────────────────────────────────────────────────────────
BLUR_FACES     = True   # Set False to draw rectangle instead of blurring
SAVE_FACES     = True   # Save each detected face as an image
ALERT_ON_FACE  = True   # Beep when a new face appears
DETECT_EYES    = True
DETECT_SMILES  = True

# ─── State ────────────────────────────────────────────────────────────────────
prev_face_count = 0
save_cooldown   = 0      # prevents saving every single frame

video_cap = cv2.VideoCapture(0)
print("Press 'q' to quit.")

while True:
    ret, frame = video_cap.read()
    if not ret:
        break

    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    faces = face_cap.detectMultiScale(gray, scaleFactor=1.3, minNeighbors=5)

    face_count = len(faces)

    # ── Alert when a new face appears ─────────────────────────────────────────
    if ALERT_ON_FACE and face_count > prev_face_count:
        winsound.Beep(1000, 200)   # frequency=1000Hz, duration=200ms
    prev_face_count = face_count

    for i, (x, y, w, h) in enumerate(faces):
        face_roi_color = frame[y:y+h, x:x+w]
        face_roi_gray  = gray[y:y+h, x:x+w]

        # ── Blur or box the face ───────────────────────────────────────────────
        if BLUR_FACES:
            blurred = cv2.GaussianBlur(face_roi_color, (99, 99), 30)
            frame[y:y+h, x:x+w] = blurred
        else:
            cv2.rectangle(frame, (x, y), (x+w, y+h), (255, 0, 0), 2)

        # Label above the face box
        cv2.putText(frame, f"Face {i+1}", (x, y - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 0, 0), 2)

        # ── Save detected face ─────────────────────────────────────────────────
        if SAVE_FACES and save_cooldown == 0:
            ts = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
            filename = os.path.join(SAVE_DIR, f"face_{i+1}_{ts}.jpg")
            cv2.imwrite(filename, face_roi_color)
            print(f"[SAVED] {filename}")

        # ── Eye detection (inside face ROI) ────────────────────────────────────
        if DETECT_EYES:
            eyes = eye_cap.detectMultiScale(face_roi_gray, 1.1, 10)
            for (ex, ey, ew, eh) in eyes:
                cv2.rectangle(face_roi_color,
                              (ex, ey), (ex+ew, ey+eh), (0, 255, 0), 1)

        # ── Smile detection (inside face ROI) ──────────────────────────────────
        if DETECT_SMILES:
            smiles = smile_cap.detectMultiScale(face_roi_gray, 1.7, 20)
            for (sx, sy, sw, sh) in smiles:
                cv2.rectangle(face_roi_color,
                              (sx, sy), (sx+sw, sy+sh), (0, 0, 255), 1)

    # Save cooldown — saves roughly once per 30 frames (~1 sec at 30fps)
    save_cooldown = (save_cooldown + 1) % 30

    # ── HUD: face count ────────────────────────────────────────────────────────
    cv2.putText(frame, f"Faces detected: {face_count}", (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 2)

    cv2.imshow("Advanced Face Detection", frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

video_cap.release()
cv2.destroyAllWindows()