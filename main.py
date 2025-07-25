import cv2
import time
import os
import threading
from emailing import send_email

# Clean images folder at startup
def clean_folder():
    for file in os.listdir("images"):
        if file.endswith(".png"):
            os.remove(os.path.join("images", file))

clean_folder()

# Initialize video capture
video = cv2.VideoCapture(0)
time.sleep(1)  # Allow camera to warm up

# Global variables
first_frame = None
status_list = []
motion_detected = False
cooldown = 30  # Email cooldown in seconds
last_email_time = 0

try:
    while True:
        # Read and process frame
        ret, frame = video.read()
        if not ret:
            break

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        gray = cv2.GaussianBlur(gray, (21, 21), 0)
        
        # Initialize background model
        if first_frame is None:
            first_frame = gray
            continue
            
        # Motion detection pipeline
        delta = cv2.absdiff(first_frame, gray)
        thresh = cv2.threshold(delta, 60, 255, cv2.THRESH_BINARY)[1]
        thresh = cv2.dilate(thresh, None, iterations=2)
        
        # Find and process contours
        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        current_status = 0
        for contour in contours:
            if cv2.contourArea(contour) < 5000:
                continue
                
            # Draw detection markers
            x, y, w, h = cv2.boundingRect(contour)
            cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
            current_status = 1
        
        # Update status tracking
        status_list.append(current_status)
        status_list = status_list[-2:]
        
        # Motion start/end detection
        if status_list[-1] == 1 and not motion_detected:
            motion_detected = True
            timestamp = int(time.time())
            image_path = f"images/motion_{timestamp}.png"
            cv2.imwrite(image_path, frame)
            
        elif status_list[-1] == 0 and motion_detected:
            motion_detected = False
            current_time = time.time()
            
            # Apply email cooldown
            if current_time - last_email_time >= cooldown:
                email_thread = threading.Thread(
                    target=send_email,
                    args=(image_path,)
                )
                email_thread.daemon = True
                email_thread.start()
                last_email_time = current_time
                
            # Update background model
            first_frame = gray
        
        # Display output
        cv2.putText(frame, f"Status: {'Motion' if current_status else 'No Motion'}", 
                   (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
        cv2.imshow("Security Feed", frame)
        
        # Exit on 'q' key
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

finally:
    # Cleanup resources
    video.release()
    cv2.destroyAllWindows()