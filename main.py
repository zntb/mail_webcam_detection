import cv2
import time
import logging
import os
from pathlib import Path
from datetime import datetime
from threading import Thread, Lock
from collections import deque
import numpy as np
from email_service import EmailService
from config import Config

# Suppress Qt platform plugin warning
os.environ['QT_QPA_PLATFORM'] = 'xcb'

class MotionDetector:
    def __init__(self, config_path="config.yaml"):
        """Initialize the motion detector with configuration."""
        self.config = Config(config_path)
        self.setup_logging()
        self.setup_directories()
        
        # Motion detection parameters
        self.background_subtractor = cv2.createBackgroundSubtractorMOG2(
            detectShadows=True, varThreshold=self.config.sensitivity
        )
        self.motion_threshold = self.config.motion_threshold
        self.min_contour_area = self.config.min_contour_area
        
        # State management
        self.status_history = deque(maxlen=5)
        self.last_motion_time = 0
        self.motion_cooldown = self.config.motion_cooldown
        
        # Motion sequence tracking
        self.motion_sequence = []
        self.motion_active = False
        self.motion_start_time = 0
        self.frames_since_motion = 0
        
        # Threading
        self.email_lock = Lock()
        self.is_running = False
        
        # Email service
        self.email_service = EmailService() if self.config.email_enabled else None
        
        # Video capture
        self.video_capture = None
        
    def setup_logging(self):
        """Configure logging."""
        logging.basicConfig(
            level=getattr(logging, self.config.log_level.upper()),
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(self.config.log_file),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
        
    def initialize_camera(self):
        """Initialize the video capture device."""
        try:
            self.video_capture = cv2.VideoCapture(self.config.camera_index)
            if not self.video_capture.isOpened():
                self.logger.error(f"Failed to open camera at index {self.config.camera_index}")
                return False
                
            self.video_capture.set(cv2.CAP_PROP_FRAME_WIDTH, self.config.frame_width)
            self.video_capture.set(cv2.CAP_PROP_FRAME_HEIGHT, self.config.frame_height)
            
            actual_width = int(self.video_capture.get(cv2.CAP_PROP_FRAME_WIDTH))
            actual_height = int(self.video_capture.get(cv2.CAP_PROP_FRAME_HEIGHT))
            
            self.logger.info(f"Camera initialized at {actual_width}x{actual_height} resolution")
            return True
            
        except Exception as e:
            self.logger.error(f"Camera initialization failed: {str(e)}")
            return False
        
    def setup_directories(self):
        """Create and verify directory."""
        try:
            images_dir = Path(self.config.images_dir).absolute()
            images_dir.mkdir(parents=True, exist_ok=True)
            
            # Test write capability
            test_file = images_dir / "write_test.tmp"
            test_file.write_text("test")
            test_file.unlink()
            
            self.logger.info(f"Directory verified: {images_dir}")
                
        except Exception as e:
            self.logger.error(f"Directory setup failed: {str(e)}")
            raise
    
    def detect_motion(self, frame):
        """Detect motion in the frame."""
        try:
            fg_mask = self.background_subtractor.apply(frame)
            
            # Noise reduction
            kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
            fg_mask = cv2.morphologyEx(fg_mask, cv2.MORPH_CLOSE, kernel)
            fg_mask = cv2.morphologyEx(fg_mask, cv2.MORPH_OPEN, kernel)
            fg_mask = cv2.dilate(fg_mask, kernel, iterations=2)
            
            contours, _ = cv2.findContours(fg_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            motion_detected = False
            motion_boxes = []
            total_motion_area = 0
            
            for contour in contours:
                if len(contour) < 3:
                    continue
                    
                area = cv2.contourArea(contour)
                if area > self.min_contour_area:
                    x, y, w, h = cv2.boundingRect(contour)
                    motion_boxes.append((x, y, w, h))
                    total_motion_area += area
                    motion_detected = True
            
            return motion_detected, motion_boxes, fg_mask, total_motion_area
            
        except Exception as e:
            self.logger.error(f"Error in motion detection: {e}")
            return False, [], None, 0
            
    def save_motion_image(self, frame, motion_boxes=None):
        """Save motion image, drawing boxes if present."""
        try:
            if frame is None or not isinstance(frame, np.ndarray) or frame.size == 0:
                self.logger.error("Invalid frame for saving")
                return None

            # Draw boxes if present
            out_frame = frame.copy()
            if motion_boxes:
                for (x, y, w, h) in motion_boxes:
                    cv2.rectangle(out_frame, (x, y), (x+w, y+h), (0, 255, 0), 2)

            # Ensure proper frame format
            if len(out_frame.shape) == 2:  # Grayscale
                out_frame = cv2.cvtColor(out_frame, cv2.COLOR_GRAY2BGR)
            elif out_frame.shape[2] == 4:   # RGBA
                out_frame = cv2.cvtColor(out_frame, cv2.COLOR_RGBA2BGR)

            # Generate filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
            filename = f"motion_{timestamp}.jpg"
            filepath = Path(self.config.images_dir) / filename

            # Save image
            cv2.imwrite(str(filepath), out_frame, [cv2.IMWRITE_JPEG_QUALITY, self.config.image_quality])

            self.logger.info(f"Saved motion image: {filepath}")
            return str(filepath)

        except Exception as e:
            self.logger.error(f"Error saving image: {e}")
            return None
    
    def send_motion_alert(self, image_path):
        """Send motion alert via email if email service is enabled, then delete file."""
        if not self.email_service or not image_path:
            return

        def email_worker():
            with self.email_lock:
                try:
                    self.email_service.send_motion_alert(image_path)
                    self.logger.info("Motion alert email sent successfully")
                except Exception as e:
                    self.logger.error(f"Failed to send motion alert: {e}")
                finally:
                    try:
                        os.remove(image_path)
                        self.logger.info(f"Deleted image after sending: {image_path}")
                    except Exception as e:
                        self.logger.error(f"Failed to delete image: {e}")

        email_thread = Thread(target=email_worker, daemon=True)
        email_thread.start()
    
    def process_motion_sequence(self):
        """Process the motion sequence and save images if real motion detected."""
        if not self.motion_sequence:
            return
        
        # Require minimum number of frames with motion to consider it valid
        if len(self.motion_sequence) < 1:  # Require at least 1 frames with motion
            self.logger.info("Motion sequence too short; ignoring potential false positive")
            self.motion_sequence = []
            self.motion_active = False
            return

        # Filter out all frames with empty motion_boxes
        valid_frames = [x for x in self.motion_sequence if x.get('motion_boxes')]

        if not valid_frames:
            self.logger.info("No valid motion detected in sequence; not saving or sending image.")
            self.motion_sequence = []
            self.motion_active = False
            return

        # Optionally: Require the largest detected box to exceed a threshold
        min_large_box_area = 5000
        valid_frames = [
            x for x in valid_frames
            if any(w*h > min_large_box_area for (x0,y0,w,h) in x['motion_boxes'])
        ]
        if not valid_frames:
            self.logger.info("No sufficiently large motion detected; not saving or sending image.")
            self.motion_sequence = []
            self.motion_active = False
            return

        # Get the frame with the largest motion area
        best = max(valid_frames, key=lambda x: x['motion_area'])
        best_frame = best['frame']
        best_motion_boxes = best.get('motion_boxes', [])

        self.logger.info(f"Sending frame with {len(best_motion_boxes)} motion boxes, areas: "
                        f"{[w*h for (x,y,w,h) in best_motion_boxes]}")

        image_path = self.save_motion_image(best_frame, best_motion_boxes)

        if image_path:
            self.last_motion_time = time.time()
            if self.email_service:
                self.send_motion_alert(image_path)

        self.motion_sequence = []
        self.motion_active = False
    
    def run(self):
        """Main detection loop with robust gating and warm-up."""
        if not self.initialize_camera():
            return False

        self.is_running = True
        self.logger.info("Motion detector started")

        self.frame_count = 0
        self.warmup_frames = 60  # Increased from 30 to 60 frames for better initialization
        self.start_time = time.time()
        self.min_startup_delay = 5  # Increased from 3 to 5 seconds
        self.initialized = False  # New flag to track proper initialization

        try:
            while self.is_running:
                ret, frame = self.video_capture.read()
                if not ret:
                    self.logger.error("Failed to read frame from camera")
                    time.sleep(0.1)
                    continue

                self.frame_count += 1
                
                # Skip frames during warmup period
                if (self.frame_count <= self.warmup_frames or
                    time.time() - self.start_time < self.min_startup_delay):
                    continue
                    
                # After warmup, process one frame to initialize the background subtractor
                if not self.initialized:
                    self.detect_motion(frame)  # Process one frame but don't act on it
                    self.initialized = True
                    self.logger.info("Background subtractor initialized")
                    continue

                motion_detected, motion_boxes, fg_mask, motion_area = self.detect_motion(frame)
                current_time = time.time()

                # Only add frames with non-empty motion_boxes
                if motion_detected and motion_boxes:
                    if not self.motion_active:
                        self.motion_active = True
                        self.motion_start_time = current_time
                        self.motion_sequence = []

                    motion_frame = frame.copy()
                    self.motion_sequence.append({
                        'frame': motion_frame,
                        'timestamp': current_time,
                        'motion_area': motion_area,
                        'motion_boxes': motion_boxes
                    })
                else:
                    if self.motion_active and self.motion_sequence:
                        self.process_motion_sequence()
                    self.motion_active = False
                    self.motion_sequence = []

                # Display
                if self.config.show_video:
                    display_frame = frame.copy()
                    for (x, y, w, h) in motion_boxes:
                        cv2.rectangle(display_frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
                    cv2.imshow("Motion Detection", display_frame)
                    if cv2.waitKey(1) & 0xFF == ord('q'):
                        break

        except KeyboardInterrupt:
            self.logger.info("Received interrupt signal")
        finally:
            self.cleanup()

        return True
        
    def cleanup(self):
        """Clean up resources."""
        self.is_running = False
        if self.video_capture:
            self.video_capture.release()
        cv2.destroyAllWindows()
        self.logger.info("Motion detector stopped")

if __name__ == "__main__":
    detector = MotionDetector()
    try:
        detector.run()
    except KeyboardInterrupt:
        print("\nShutting down motion detector...")
        detector.cleanup()