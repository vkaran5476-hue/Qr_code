import cv2

face_cap = cv2.CascadeClassifier(r"C:\Users\karan\PycharmProjects\PythonProject2\.venv\Lib\site-packages\cv2\data\haarcascade_frontalface_default.xml")

video_cap = cv2.VideoCapture(0)
while True:
    ret, video_data = video_cap.read()
    col = cv2.cvtColor(video_data, cv2.COLOR_BGR2GRAY)
    faces = face_cap.detectMultiScale(col, 1.3, 5)
    for (x, y, w, h) in faces:
        cv2.rectangle(video_data, (x, y), (x + w, y + h), (255, 0, 0), 2)

    cv2.imshow("video_live", video_data)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

video_cap.release()
cv2.destroyAllWindows()