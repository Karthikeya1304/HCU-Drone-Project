import cv2

camera = cv2.VideoCapture(0)

if not camera.isOpened():
    print("ERROR: Could not open camera")
    exit()

print("Camera started. Press 'q' to quit.")

while True:
    ret, frame = camera.read()

    if not ret:
        print("ERROR: Could not read frame")
        break

    cv2.imshow("Robot Vision Camera", frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

camera.release()
cv2.destroyAllWindows()
