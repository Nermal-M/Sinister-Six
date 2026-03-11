from flask import Flask, render_template, request, jsonify, send_file, url_for
from werkzeug.utils import secure_filename
from pathlib import Path
import cv2
import numpy as np
from ultralytics import YOLO
import json
import os
from datetime import datetime
import torch
import traceback
from dotenv import load_dotenv, find_dotenv
from analysis import extract_video_analysis, generate_summary

# Load environment variables (search parent directories)
load_dotenv(find_dotenv())
API_VIDEO_KEY = os.getenv('API_VIDEO_KEY') or 'voSJ4O5ldRMfv9OWEK9qThiHlWXAuEQEEssLSauuJGM'

app = Flask(__name__)

# Configuration
UPLOAD_FOLDER = Path(__file__).parent / 'static' / 'uploads'
OUTPUT_FOLDER = Path(__file__).parent / 'static' / 'outputs'
ALLOWED_EXTENSIONS = {'mp4', 'avi', 'mov', 'mkv'}
MAX_FILE_SIZE = 500 * 1024 * 1024  # 500MB

UPLOAD_FOLDER.mkdir(parents=True, exist_ok=True)
OUTPUT_FOLDER.mkdir(parents=True, exist_ok=True)

app.config['UPLOAD_FOLDER'] = str(UPLOAD_FOLDER)
app.config['OUTPUT_FOLDER'] = str(OUTPUT_FOLDER)
app.config['MAX_CONTENT_LENGTH'] = MAX_FILE_SIZE

# Global model variable
model = None

# Bag Tracker Class
class BagTracker:
    def __init__(self, initial_bbox, distance_threshold=50):
        self.initial_bbox = initial_bbox
        self.current_bbox = initial_bbox
        self.current_center = ((initial_bbox[0] + initial_bbox[2]) // 2,
                              (initial_bbox[1] + initial_bbox[3]) // 2)
        self.distance_threshold = distance_threshold
        self.track_history = [self.current_center]
        self.lost_frames = 0
        self.is_tracking = True
    
    def update(self, detections):
        if not detections:
            self.is_tracking = False
            self.lost_frames += 1
            return
        
        current_x, current_y = self.current_center
        closest_detection = None
        min_distance = float('inf')
        
        for detection in detections:
            det_x, det_y = detection['center']
            distance = np.sqrt((det_x - current_x)**2 + (det_y - current_y)**2)
            
            if distance < min_distance and distance <= self.distance_threshold:
                min_distance = distance
                closest_detection = detection
        
        if closest_detection:
            self.current_bbox = closest_detection['bbox']
            self.current_center = closest_detection['center']
            self.track_history.append(self.current_center)
            self.is_tracking = True
        else:
            self.is_tracking = False
            self.lost_frames += 1
    
    def draw_on_frame(self, frame, detections):
        frame_vis = frame.copy()
        
        if self.is_tracking:
            x1, y1, x2, y2 = self.current_bbox
            cv2.rectangle(frame_vis, (x1, y1), (x2, y2), (0, 0, 255), 2)
            
            label = "TRACKED BAG"
            cv2.putText(frame_vis, label, (x1, y1 - 10),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)
            
            cx, cy = self.current_center
            cv2.circle(frame_vis, (cx, cy), 6, (0, 0, 255), -1)
        else:
            cv2.putText(frame_vis, "TRACKING LOST", (50, 50),
                       cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 0, 255), 2)
        
        if len(self.track_history) > 1:
            points = np.array(self.track_history[-30:], dtype=np.int32)
            cv2.polylines(frame_vis, [points], False, (0, 255, 255), 2)
        
        return frame_vis

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def load_model():
    global model
    try:
        best_model_path = Path(__file__).parent.parent / "runs" / "detect" / "bag_detection" / "weights" / "best.pt"
        if best_model_path.exists():
            model = YOLO(str(best_model_path))
            return True
    except Exception as e:
        print(f"Error loading model: {e}")
    return False

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/detect-bags', methods=['POST'])
def detect_bags():
    """Detect bags in the first frame of uploaded video"""
    try:
        if 'video' not in request.files:
            return jsonify({'error': 'No video file provided'}), 400
        
        file = request.files['video']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        if not allowed_file(file.filename):
            return jsonify({'error': 'Invalid file type. Allowed: mp4, avi, mov, mkv'}), 400
        
        # Load model if not already loaded
        if model is None:
            if not load_model():
                return jsonify({'error': 'Could not load YOLO model'}), 500
        
        # Save uploaded file
        filename = secure_filename(file.filename)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_')
        filepath = UPLOAD_FOLDER / (timestamp + filename)
        file.save(str(filepath))
        
        # Extract first frame and detect bags
        cap = cv2.VideoCapture(str(filepath))
        ret, first_frame = cap.read()
        
        if not ret:
            return jsonify({'error': 'Could not read video file'}), 400
        
        # Get video properties
        fps = cap.get(cv2.CAP_PROP_FPS)
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        duration = total_frames / fps if fps > 0 else 0
        
        cap.release()
        
        # Run YOLO detection
        results = model(first_frame, verbose=False, conf=0.5)
        
        # Parse detections
        detections = []
        for result in results:
            for box in result.boxes:
                class_id = int(box.cls[0])
                confidence = float(box.conf[0])
                x1, y1, x2, y2 = map(int, box.xyxy[0])
                
                detection = {
                    'class': model.names[class_id],
                    'class_id': class_id,
                    'confidence': confidence,
                    'bbox': (x1, y1, x2, y2),
                    'center': ((x1 + x2) // 2, (y1 + y2) // 2),
                    'width': x2 - x1,
                    'height': y2 - y1,
                    'area': (x2 - x1) * (y2 - y1)
                }
                detections.append(detection)
        
        # Filter bags and persons
        bags = [d for d in detections if d['class'] == 'Bag']
        persons = [d for d in detections if d['class'] == 'Person']
        bags.sort(key=lambda x: x['area'], reverse=True)
        
        # Generate thumbnails for each bag
        bag_list = []
        for i, bag in enumerate(bags):
            x1, y1, x2, y2 = bag['bbox']
            roi = first_frame[max(0, y1-20):min(first_frame.shape[0], y2+20),
                            max(0, x1-20):min(first_frame.shape[1], x2+20)]
            
            img_filename = f"{timestamp}bag_{i}.jpg"
            img_path = OUTPUT_FOLDER / img_filename
            cv2.imwrite(str(img_path), roi)
            
            bag_list.append({
                'index': i,
                'confidence': float(bag['confidence']),
                'center': bag['center'],
                'width': bag['width'],
                'height': bag['height'],
                'area': bag['area'],
                'image_path': f"outputs/{img_filename}"
            })
        
        return jsonify({
            'success': True,
            'video_path': str(filepath),
            'video_info': {
                'filename': filename,
                'fps': fps,
                'width': width,
                'height': height,
                'total_frames': total_frames,
                'duration': duration
            },
            'bags': bag_list,
            'total_detections': len(detections),
            'persons': len(persons)
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/track-bag', methods=['POST'])
def track_bag():
    """Track selected bag through video"""
    try:
        data = request.json
        video_path = data.get('video_path')
        bag_index = data.get('bag_index', 0)
        
        if not video_path or not Path(video_path).exists():
            return jsonify({'error': 'Invalid video path'}), 400
        
        if model is None:
            if not load_model():
                return jsonify({'error': 'Could not load model'}), 500
        
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            return jsonify({'error': 'Could not open video'}), 400
        
        fps = cap.get(cv2.CAP_PROP_FPS)
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        
        # Get first frame for bag detection
        ret, first_frame = cap.read()
        if not ret:
            return jsonify({'error': 'Could not read first frame'}), 400
        
        # Detect bags in first frame
        results = model(first_frame, verbose=False, conf=0.5)
        
        bags = []
        for result in results:
            for box in result.boxes:
                class_id = int(box.cls[0])
                if model.names[class_id] == 'Bag':
                    confidence = float(box.conf[0])
                    x1, y1, x2, y2 = map(int, box.xyxy[0])
                    bags.append({
                        'bbox': (x1, y1, x2, y2),
                        'center': ((x1 + x2) // 2, (y1 + y2) // 2),
                        'confidence': confidence
                    })
        
        if bag_index >= len(bags):
            return jsonify({'error': f'Bag index {bag_index} not found'}), 400
        
        # Initialize tracker
        initial_bbox = bags[bag_index]['bbox']
        tracker = BagTracker(initial_bbox, distance_threshold=50)
        
        # Reset video
        cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
        
        # Define output path
        input_path = Path(video_path)
        output_filename = f"tracked_{input_path.stem}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp4"
        output_path = OUTPUT_FOLDER / output_filename
        
        # Setup video writer
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(str(output_path), fourcc, fps, (width, height))
        
        frame_count = 0
        processed_frames = 0
        
        # Process each frame
        while frame_count < total_frames:
            ret, frame = cap.read()
            if not ret:
                break
            
            frame_count += 1
            
            # Detect bags in current frame
            results = model(frame, verbose=False, conf=0.5)
            
            # Parse detections
            frame_detections = []
            for result in results:
                for box in result.boxes:
                    class_id = int(box.cls[0])
                    if model.names[class_id] == 'Bag':
                        confidence = float(box.conf[0])
                        x1, y1, x2, y2 = map(int, box.xyxy[0])
                        detection = {
                            'confidence': confidence,
                            'bbox': (x1, y1, x2, y2),
                            'center': ((x1 + x2) // 2, (y1 + y2) // 2)
                        }
                        frame_detections.append(detection)
            
            # Update tracker
            tracker.update(frame_detections)
            
            # Draw on frame
            frame_output = tracker.draw_on_frame(frame, frame_detections)
            
            # Write to output video
            out.write(frame_output)
            processed_frames += 1
        
        # Cleanup
        cap.release()
        out.release()
        
        return jsonify({
            'success': True,
            'output_video': url_for('download_file', filename=output_filename),
            'stats': {
                'total_frames': processed_frames,
                'lost_frames': tracker.lost_frames,
                'reliability': ((processed_frames - tracker.lost_frames) / processed_frames * 100) if processed_frames > 0 else 0,
                'tracking_points': len(tracker.track_history)
            }
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/summarizer')
def summarizer():
    return render_template('summarizer.html')

@app.route('/api/summarize-video', methods=['POST'])
def summarize_video():
    """Analyze tracked video using local behavioral inference"""
    try:
        data = request.json
        video_path = data.get('video_path')
        
        print(f"[SUMMARIZE] Received request for: {video_path}")
        
        if not video_path:
            return jsonify({'error': 'No video path provided'}), 400
        
        # Convert URL path to file system path
        if video_path.startswith('/download/'):
            filename = video_path.replace('/download/', '')
            filepath = OUTPUT_FOLDER / filename
        else:
            filepath = Path(video_path)
        
        print(f"[SUMMARIZE] Resolved filepath: {filepath}")
        
        if not filepath.exists():
            print(f"[SUMMARIZE] File not found: {filepath}")
            return jsonify({'error': f'Video file not found: {filepath.name}'}), 400
        
        # Load model if needed
        if model is None:
            print("[SUMMARIZE] Loading YOLO model...")
            if not load_model():
                return jsonify({'error': 'Could not load detection model'}), 500
        
        print("[SUMMARIZE] Extracting video analysis...")
        # Extract comprehensive video analysis
        analysis_data = extract_video_analysis(str(filepath), model)
        if not analysis_data:
            print("[SUMMARIZE] Analysis failed - no data returned")
            return jsonify({'error': 'Could not analyze video'}), 400
        
        print(f"[SUMMARIZE] Analysis complete. Bag status: {analysis_data.get('bag_status')}")
        
        # Generate summary using local behavioral inference
        summary, error = generate_summary(analysis_data)
        if error:
            print(f"[SUMMARIZE] Summary generation error: {error}")
            return jsonify({'error': f'Summary generation error: {error}'}), 500
        
        if not summary:
            print("[SUMMARIZE] No summary generated")
            return jsonify({'error': 'Summary generation failed - no content'}), 500
        
        behavior = analysis_data.get('behavior', {})
        
        # Determine movement pattern
        mobility = behavior.get('mobility_ratio', 0)
        if mobility > 0.7:
            movement_pattern = 'Mostly Stationary'
        elif mobility < 0.3:
            movement_pattern = 'Highly Mobile'
        else:
            movement_pattern = 'Mixed Movement'
        
        print("[SUMMARIZE] Summary generated successfully")
        
        return jsonify({
            'success': True,
            'summary': summary,
            'analysis': {
                'duration': analysis_data['duration'],
                'fps': analysis_data['fps'],
                'total_frames': analysis_data['total_frames'],
                'bag_status': analysis_data['bag_status'],
                'frames_with_person': behavior.get('frames_with_person', 0),
                'frames_unattended': behavior.get('frames_unattended', 0),
                'trajectory_points': len(analysis_data.get('bag_trajectory', [])),
                'total_distance': behavior.get('total_movement', 0),
                'movement_pattern': movement_pattern,
                'avg_speed': behavior.get('avg_speed', 0),
                'max_speed': behavior.get('max_speed', 0),
                'avg_proximity': behavior.get('avg_proximity'),
                'num_approaches': behavior.get('num_approaches', 0),
                'num_departures': behavior.get('num_departures', 0)
            }
        })
    
    except Exception as e:
        print(f"[SUMMARIZE] Exception: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/download/<filename>')
def download_file(filename):
    """Download tracked video"""
    try:
        filepath = OUTPUT_FOLDER / secure_filename(filename)
        if filepath.exists():
            return send_file(str(filepath), as_attachment=True)
        return jsonify({'error': 'File not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    load_model()
    app.run(debug=True, host='127.0.0.1', port=5001)
