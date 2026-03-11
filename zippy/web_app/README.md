# Bag Detection & Tracking Web Application

A comprehensive web application for detecting and tracking bags in surveillance video footage using YOLOv8 object detection and video summarization.

## Features

### 1. **Bag Detection & Tracking Module**
- Upload surveillance videos (MP4, AVI, MOV, MKV)
- Automatically detect all bags and people in the first frame
- Select specific bag by index to track
- Track selected bag throughout entire video
- Generate output video with tracking visualization
- Download tracked video

### 2. **Video Summarizer Module**
- Upload tracked video for analysis
- Analyze video contents using YOLO detection
- Generate comprehensive summary report
- Display detection statistics (bags, people detected)
- Download summary report as text file

## Installation

### Prerequisites
- Python 3.8+
- CUDA compatible GPU (optional, for faster processing)

### Setup Steps

1. **Navigate to web_app directory**
```bash
cd d:\Yolooo\web_app
```

2. **Create virtual environment (optional but recommended)**
```bash
python -m venv venv
venv\Scripts\activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Ensure model files exist**
- Place `best.pt` at: `d:\Yolooo\runs\detect\bag_detection\weights\best.pt`
- Or use fallback: `d:\Yolooo\yolov8n.pt`

5. **Run the application**
```bash
python app.py
```

6. **Open in browser**
```
http://localhost:5000
```

## Usage

### Detection & Tracking Workflow

1. **Upload Video**
   - Click upload area or drag-drop video file
   - Supported formats: MP4, AVI, MOV, MKV
   - Maximum file size: 500MB

2. **Detect Bags**
   - System automatically analyzes first frame
   - Displays detected bags with confidence scores
   - Shows video properties (duration, resolution, FPS)

3. **Select Bag**
   - Click on bag card to select
   - Shows bag position, size, and confidence
   - Only one bag can be tracked per video

4. **Track Bag**
   - Click "Start Tracking" button
   - System processes entire video frame-by-frame
   - Applies YOLO detection on each frame
   - Matches and tracks selected bag

5. **Download Results**
   - Download tracked video with visualization
   - Includes statistics on tracking reliability
   - Shows number of frames lost during tracking

### Video Summarizer Workflow

1. **Upload Tracked Video**
   - Upload video from detection/tracking module
   - Or upload any surveillance video

2. **Analyze Video**
   - Click "Analyze Video" button
   - System samples frames and detects objects
   - Generates comprehensive analysis

3. **View Summary**
   - Read generated summary report
   - View detection statistics
   - See video properties

4. **Download Report**
   - Download summary as text file
   - Contains all analysis data and statistics

## Project Structure

```
web_app/
├── app.py                           # Flask backend application
├── requirements.txt                 # Python dependencies
├── README.md                        # This file
├── templates/
│   ├── index.html                  # Detection & tracking interface
│   └── summarizer.html             # Video summarizer interface
├── static/
│   ├── css/
│   │   └── style.css               # Application styling
│   ├── js/
│   │   ├── detection.js            # Detection & tracking logic
│   │   └── summarizer.js           # Summarizer logic
│   ├── uploads/                    # Temporary uploaded videos
│   └── outputs/                    # Generated tracked videos
```

## Technical Details

### Backend (Flask)
- **Language**: Python 3
- **Framework**: Flask
- **Video Processing**: OpenCV (cv2)
- **Object Detection**: YOLOv8
- **File Handling**: Werkzeug

### Frontend
- **HTML5** for structure
- **CSS3** for styling with responsive design
- **JavaScript** for interactivity
- **Fetch API** for backend communication

### Core Algorithms

#### BagTracker Class
Implements centroid tracking algorithm:
- Matches detections between frames based on distance
- Maintains tracking history as list of centroids
- Tracks lost frames when bag detection fails
- Supports distance threshold for robustness

#### Detection Pipeline
1. Load YOLO model (best.pt or yolov8n.pt)
2. Run inference on each video frame
3. Filter detections by class (Bag, Person)
4. Parse bounding boxes and confidence scores
5. Match to tracked object using distance metric

## Configuration

### Model Selection
By default, application tries to load:
1. Fine-tuned model: `runs/detect/bag_detection/weights/best.pt`
2. Fallback model: `yolov8n.pt` (YOLOv8 Nano)

### Detection Parameters
- **Confidence Threshold**: 0.5 (50%)
- **Distance Threshold**: 50 pixels
- **Max Tracking Loss**: No limit (counted in statistics)

### Processing Parameters
- **Output Video Codec**: mp4v (MPEG-4)
- **Output Directory**: `static/outputs/`
- **Temporary Files**: `static/uploads/`

## Troubleshooting

### Model Not Loading
- Ensure YOLO model file exists
- Check file permissions
- Verify model path in app.py

### Video Processing Slow
- Use GPU if available (CUDA enabled PyTorch)
- Reduce video resolution
- Process shorter videos first

### Out of Memory
- Process shorter videos
- Ensure sufficient RAM available
- Close other applications

## API Endpoints

### Detection & Tracking
- **POST** `/api/detect-bags` - Upload and detect bags in first frame
- **POST** `/api/track-bag` - Track selected bag throughout video
- **GET** `/download/<filename>` - Download tracked video

### Summarization
- **POST** `/api/summarize-video` - Analyze and summarize video
- **GET** `/summarizer` - Video summarizer page

## Performance

### Typical Processing Times (on GPU)
- Detection on first frame: 1-2 seconds
- Tracking full video (5 min @ 30fps): 2-5 minutes
- Video summarization: 1-3 minutes

### Memory Requirements
- Minimum RAM: 4GB
- Recommended RAM: 8GB+
- GPU VRAM: 2GB+ (for faster processing)

## Known Limitations

1. **Single Bag Tracking**: Only one bag per video
2. **Occlusion Handling**: Limited - tracker may lose bag if fully occluded
3. **Frame Rate**: Works with any FPS but processing time scales linearly
4. **Video Formats**: Limited to common formats (MP4, AVI, MOV, MKV)

## Future Enhancements

- [ ] Multi-object tracking (track multiple bags)
- [ ] Advanced occlusion handling
- [ ] Real-time video processing
- [ ] Cloud-based processing
- [ ] Video streaming support
- [ ] Advanced summarization (AI-powered)

## License

This project uses YOLOv8 from Ultralytics (AGPL-3.0 License)

## Support

For issues or questions:
1. Check troubleshooting section
2. Review application logs
3. Verify model files and dependencies
4. Check video file integrity

## Credits

- **YOLOv8**: Ultralytics
- **OpenCV**: Intel
- **PyTorch**: Meta AI
- **Flask**: Pallets

---

**Last Updated**: January 2024
**Version**: 1.0.0
