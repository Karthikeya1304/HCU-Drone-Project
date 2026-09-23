import cv2
import numpy as np

camera = cv2.VideoCapture(0)

if not camera.isOpened():
    print("ERROR: Could not open camera")
    exit()

# Create HSV adjustment window
cv2.namedWindow("HSV Controls")

def nothing(x):
    pass

# Lower HSV values
cv2.createTrackbar("H Low", "HSV Controls", 0, 179, nothing)
cv2.createTrackbar("S Low", "HSV Controls", 80, 255, nothing)
cv2.createTrackbar("V Low", "HSV Controls", 50, 255, nothing)

# Upper HSV values
cv2.createTrackbar("H High", "HSV Controls", 10, 179, nothing)
cv2.createTrackbar("S High", "HSV Controls", 255, 255, nothing)
cv2.createTrackbar("V High", "HSV Controls", 255, 255, nothing)

print("Red object detection started.")
print("Adjust HSV sliders until only the red object appears in the Mask window.")
print("Press q to quit.")

while True:

    ret, frame = camera.read()

    if not ret:
        print("ERROR: Could not read camera frame")
        break

    # Flip image horizontally for easier interaction
    frame = cv2.flip(frame, 1)

    # Reduce image noise
    blurred = cv2.GaussianBlur(frame, (7, 7), 0)

    # Convert BGR -> HSV
    hsv = cv2.cvtColor(blurred, cv2.COLOR_BGR2HSV)

    # Read slider values
    h_low = cv2.getTrackbarPos("H Low", "HSV Controls")
    s_low = cv2.getTrackbarPos("S Low", "HSV Controls")
    v_low = cv2.getTrackbarPos("V Low", "HSV Controls")

    h_high = cv2.getTrackbarPos("H High", "HSV Controls")
    s_high = cv2.getTrackbarPos("S High", "HSV Controls")
    v_high = cv2.getTrackbarPos("V High", "HSV Controls")

    lower = np.array([h_low, s_low, v_low])
    upper = np.array([h_high, s_high, v_high])

    # Create mask
    mask = cv2.inRange(hsv, lower, upper)

    # Remove noise
    kernel = np.ones((7, 7), np.uint8)

    mask = cv2.morphologyEx(
        mask,
        cv2.MORPH_OPEN,
        kernel
    )

    mask = cv2.morphologyEx(
        mask,
        cv2.MORPH_CLOSE,
        kernel
    )

    # Find contours
    contours, _ = cv2.findContours(
        mask,
        cv2.RETR_EXTERNAL,
        cv2.CHAIN_APPROX_SIMPLE
    )

    # Find largest useful object
    best_contour = None
    best_area = 0

    for contour in contours:

        area = cv2.contourArea(contour)

        if area > best_area:
            best_area = area
            best_contour = contour

    if best_contour is not None and best_area > 500:

        x, y, w, h = cv2.boundingRect(best_contour)

        # Calculate center
        center_x = x + w // 2
        center_y = y + h // 2

        # Draw bounding box
        cv2.rectangle(
            frame,
            (x, y),
            (x + w, y + h),
            (0, 255, 0),
            2
        )

        # Draw center
        cv2.circle(
            frame,
            (center_x, center_y),
            7,
            (255, 0, 0),
            -1
        )

        # Display coordinates
        cv2.putText(
            frame,
            f"Center: ({center_x}, {center_y})",
            (x, max(y - 10, 30)),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (0, 255, 0),
            2
        )

        cv2.putText(
            frame,
            f"Area: {int(best_area)}",
            (x, y + h + 25),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (0, 255, 0),
            2
        )

    # Show results
    cv2.imshow("Robot Vision", frame)
    cv2.imshow("Mask", mask)

    key = cv2.waitKey(1) & 0xFF

    if key == ord("q"):
        break

camera.release()
cv2.destroyAllWindows()
