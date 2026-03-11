// Detection and Tracking JavaScript

let uploadedVideoPath = null;
let detectedBags = [];
let selectedBagIndex = null;
let trackedVideoPath = null;

// Upload Area Setup
const uploadArea = document.getElementById('uploadArea');
const videoInput = document.getElementById('videoInput');
const uploadStatus = document.getElementById('uploadStatus');
const statusMessage = document.getElementById('statusMessage');
const detectStep = document.getElementById('detectStep');
const detectBtn = document.getElementById('detectBtn');
const detectionResults = document.getElementById('detectionResults');
const bagsList = document.getElementById('bagsList');
const selectStep = document.getElementById('selectStep');
const bagSelector = document.getElementById('bagSelector');
const trackStep = document.getElementById('trackStep');
const trackBtn = document.getElementById('trackBtn');
const trackingProgress = document.getElementById('trackingProgress');
const progressFill = document.getElementById('progressFill');
const progressText = document.getElementById('progressText');
const trackingResults = document.getElementById('trackingResults');
const trackingStats = document.getElementById('trackingStats');
const downloadLink = document.getElementById('downloadLink');

// Summary elements
const summaryStep = document.getElementById('summaryStep');
const summarizeBtn = document.getElementById('summarizeBtn');
const summaryProgress = document.getElementById('summaryProgress');
const summaryProgressFill = document.getElementById('summaryProgressFill');
const summaryProgressText = document.getElementById('summaryProgressText');
const summaryResults = document.getElementById('summaryResults');
const summaryText = document.getElementById('summaryText');
const summaryStats = document.getElementById('summaryStats');
const downloadReport = document.getElementById('downloadReport');

// Drag and drop handlers
uploadArea.addEventListener('dragover', (e) => {
    e.preventDefault();
    uploadArea.classList.add('dragover');
});

uploadArea.addEventListener('dragleave', () => {
    uploadArea.classList.remove('dragover');
});

uploadArea.addEventListener('drop', (e) => {
    e.preventDefault();
    uploadArea.classList.remove('dragover');
    const files = e.dataTransfer.files;
    if (files.length > 0) {
        handleFileUpload(files[0]);
    }
});

uploadArea.addEventListener('click', () => {
    videoInput.click();
});

videoInput.addEventListener('change', (e) => {
    if (e.target.files.length > 0) {
        handleFileUpload(e.target.files[0]);
    }
});

function handleFileUpload(file) {
    // Validate file
    const validTypes = ['video/mp4', 'video/avi', 'video/quicktime', 'video/x-msvideo'];
    if (!validTypes.some(type => file.type.includes(type)) && !file.name.match(/\.(mp4|avi|mov|mkv)$/i)) {
        showStatus('error', 'Invalid file type. Please upload MP4, AVI, MOV, or MKV.');
        return;
    }

    if (file.size > 500 * 1024 * 1024) {
        showStatus('error', 'File size exceeds 500MB limit.');
        return;
    }

    // Create FormData and upload
    const formData = new FormData();
    formData.append('video', file);

    showStatus('loading', 'Uploading and analyzing video...');
    
    fetch('/api/detect-bags', {
        method: 'POST',
        body: formData
    })
    .then(response => {
        if (!response.ok) {
            return response.json().then(data => {
                throw new Error(data.error || `HTTP ${response.status}: ${response.statusText}`);
            });
        }
        return response.json();
    })
    .then(data => {
        if (data.success) {
            uploadedVideoPath = data.video_path;
            detectedBags = data.bags || [];
            
            if (!data.bags || !Array.isArray(data.bags)) {
                showStatus('error', 'Invalid response format from server');
                return;
            }
            
            showStatus('success', `Video uploaded successfully! Detected ${data.bags.length} bags and ${data.persons || 0} persons.`);
            
            // Show detection results
            detectStep.style.display = 'block';
            
            // Automatically detect
            detectBags(data);
        } else {
            showStatus('error', data.error || 'Failed to upload video');
        }
    })
    .catch(error => {
        console.error('Upload error:', error);
        showStatus('error', 'Error uploading video: ' + error.message);
    });
}

function showStatus(type, message) {
    uploadStatus.style.display = 'block';
    statusMessage.textContent = message;
    statusMessage.className = `status-message ${type}`;
}

function detectBags(data) {
    // Validate response data structure
    if (!data || !data.video_info || !Array.isArray(data.bags)) {
        showStatus('error', 'Invalid server response: missing required fields');
        console.error('Invalid data structure:', data);
        return;
    }
    
    const detectionInfo = document.getElementById('detectionInfo');
    
    try {
        detectionInfo.innerHTML = `
            <strong>Detection Results:</strong><br>
            Total objects detected: ${data.total_detections || 0}<br>
            Bags detected: ${data.bags.length}<br>
            People detected: ${data.persons || 0}<br>
            <br>
            Video Information:<br>
            Duration: ${(data.video_info.duration || 0).toFixed(2)} seconds<br>
            Resolution: ${data.video_info.width || 0}×${data.video_info.height || 0}<br>
            FPS: ${(data.video_info.fps || 0).toFixed(2)}<br>
            Total Frames: ${data.video_info.total_frames || 0}
        `;
    } catch (error) {
        showStatus('error', 'Error displaying detection results: ' + error.message);
        console.error('Detection info error:', error);
        return;
    }
    
    // Display bags list
    bagsList.innerHTML = '';
    data.bags.forEach((bag, index) => {
        const bagItem = document.createElement('div');
        bagItem.className = 'bag-item';
        
        const imageUrl = bag.image_path ? `/static/${bag.image_path}` : '';
        
        bagItem.innerHTML = `
            <div class="bag-image-container">
                ${imageUrl ? `<img src="${imageUrl}" alt="Bag ${index}" class="bag-thumbnail">` : '<div style="background:#ccc;height:100px;display:flex;align-items:center;justify-content:center;">No Image</div>'}
            </div>
            <div class="bag-details">
                <div class="bag-info">
                    <span class="bag-label">Bag ${index}</span>
                </div>
                <div class="bag-info">
                    <span class="bag-label">Confidence:</span>
                    <span class="bag-value">${((bag.confidence || 0) * 100).toFixed(2)}%</span>
                </div>
                <div class="bag-info">
                    <span class="bag-label">Position:</span>
                    <span class="bag-value">(${(bag.center ? bag.center[0] : 0)}, ${(bag.center ? bag.center[1] : 0)})</span>
                </div>
                <div class="bag-info">
                    <span class="bag-label">Size:</span>
                    <span class="bag-value">${bag.width || 0}×${bag.height || 0}</span>
                </div>
                <div class="bag-info">
                    <span class="bag-label">Area:</span>
                    <span class="bag-value">${bag.area || 0} px²</span>
                </div>
            </div>
        `;
        bagsList.appendChild(bagItem);
    });
    
    detectionResults.style.display = 'block';
    
    // Show select step if bags found
    if (data.bags.length > 0) {
        selectStep.style.display = 'block';
        displayBagSelector(data.bags);
    } else {
        showStatus('warning', 'No bags detected in the video. Please try a different video.');
    }
}

function displayBagSelector(bags) {
    if (!Array.isArray(bags) || bags.length === 0) {
        bagSelector.innerHTML = '<p>No bags available to select.</p>';
        return;
    }
    
    bagSelector.innerHTML = '';
    bags.forEach((bag, index) => {
        const bagCard = document.createElement('div');
        bagCard.className = 'bag-card';
        bagCard.innerHTML = `
            <div class="bag-title">Bag ${index}</div>
            <div class="bag-detail">
                <span class="detail-label">Confidence:</span>
                <span class="detail-value">${((bag.confidence || 0) * 100).toFixed(2)}%</span>
            </div>
            <div class="bag-detail">
                <span class="detail-label">Position:</span>
                <span class="detail-value">(${(bag.center ? bag.center[0] : 0)}, ${(bag.center ? bag.center[1] : 0)})</span>
            </div>
            <div class="bag-detail">
                <span class="detail-label">Width:</span>
                <span class="detail-value">${bag.width || 0}px</span>
            </div>
            <div class="bag-detail">
                <span class="detail-label">Height:</span>
                <span class="detail-value">${bag.height || 0}px</span>
            </div>
            <div class="bag-detail">
                <span class="detail-label">Area:</span>
                <span class="detail-value">${bag.area || 0}px²</span>
            </div>
            <button class="btn btn-primary" style="width: 100%; margin-top: 1rem;">Select This Bag</button>
        `;
        
        const selectButton = bagCard.querySelector('button');
        selectButton.addEventListener('click', () => {
            selectBag(index, bagCard);
        });
        
        bagSelector.appendChild(bagCard);
    });
}

function selectBag(index, element) {
    // Remove previous selection
    document.querySelectorAll('.bag-card').forEach(card => {
        card.classList.remove('selected');
    });
    
    // Add selection to clicked card
    element.classList.add('selected');
    selectedBagIndex = index;
    
    // Show tracking step
    trackStep.style.display = 'block';
    showStatus('success', `Bag ${index} selected! Click "Start Tracking" to process the video.`);
}

detectBtn.addEventListener('click', () => {
    if (detectedBags.length === 0) {
        showStatus('error', 'No bags detected. Please upload a different video.');
    }
});

trackBtn.addEventListener('click', () => {
    if (selectedBagIndex === null) {
        showStatus('error', 'Please select a bag first.');
        return;
    }
    
    trackBag();
});

function trackBag() {
    trackBtn.disabled = true;
    trackingProgress.style.display = 'block';
    trackingResults.style.display = 'none';
    
    const requestData = {
        video_path: uploadedVideoPath,
        bag_index: selectedBagIndex
    };
    
    // Simulate progress
    let progress = 0;
    const progressInterval = setInterval(() => {
        if (progress < 90) {
            progress += Math.random() * 30;
            if (progress > 90) progress = 90;
            updateProgress(progress);
        }
    }, 500);
    
    fetch('/api/track-bag', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(requestData)
    })
    .then(response => response.json())
    .then(data => {
        clearInterval(progressInterval);
        updateProgress(100);
        
        if (data.success) {
            showStatus('success', 'Tracking completed successfully!');
            displayTrackingResults(data);
            trackingResults.style.display = 'block';
            
            // Set download link
            downloadLink.href = data.output_video;
            downloadLink.download = `tracked_video_${new Date().getTime()}.mp4`;
        } else {
            showStatus('error', data.error || 'Tracking failed');
        }
        
        trackBtn.disabled = false;
    })
    .catch(error => {
        clearInterval(progressInterval);
        showStatus('error', 'Error: ' + error.message);
        trackBtn.disabled = false;
    });
}

function updateProgress(percent) {
    progressFill.style.width = percent + '%';
    progressText.textContent = `Processing... ${Math.round(percent)}%`;
}

function displayTrackingResults(data) {
    // Hide statistics, just keep the heading
    trackingStats.innerHTML = '';
    
    // Store tracked video path and show summary step
    trackedVideoPath = data.output_video;
    summaryStep.style.display = 'block';
}

// Summary functionality
summarizeBtn.addEventListener('click', generateSummary);

downloadReport.addEventListener('click', () => {
    if (!summaryResults.style.display || summaryResults.style.display === 'none') {
        return;
    }
    
    const reportContent = document.getElementById('summaryText').textContent;
    const statsContent = document.getElementById('summaryStats').textContent;
    
    const fullReport = `BAG TRACKING VIDEO ANALYSIS REPORT
Generated: ${new Date().toLocaleString()}
=====================================

${reportContent}

${statsContent}
`;
    
    const blob = new Blob([fullReport], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `analysis_report_${new Date().getTime()}.txt`;
    a.click();
    URL.revokeObjectURL(url);
});

function generateSummary() {
    if (!trackedVideoPath) {
        showStatus('error', 'No tracked video available. Please track a bag first.');
        return;
    }
    
    console.log('Generating summary for:', trackedVideoPath);
    
    summarizeBtn.disabled = true;
    summaryProgress.style.display = 'block';
    summaryResults.style.display = 'none';
    
    // Simulate progress
    let progress = 0;
    const progressInterval = setInterval(() => {
        if (progress < 90) {
            progress += Math.random() * 15;
            updateSummaryProgress(Math.min(progress, 90));
        }
    }, 500);
    
    fetch('/api/summarize-video', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            video_path: trackedVideoPath
        })
    })
    .then(response => {
        console.log('Summary response status:', response.status);
        if (!response.ok) {
            return response.json().then(data => {
                throw new Error(data.error || `HTTP ${response.status}`);
            });
        }
        return response.json();
    })
    .then(data => {
        console.log('Summary data received:', data);
        clearInterval(progressInterval);
        updateSummaryProgress(100);
        
        setTimeout(() => {
            summaryProgress.style.display = 'none';
            
            if (data.success && data.summary) {
                displaySummary(data);
                summaryResults.style.display = 'block';
                showStatus('success', 'Summary generated successfully!');
            } else {
                showStatus('error', data.error || 'Failed to generate summary');
            }
            
            summarizeBtn.disabled = false;
        }, 500);
    })
    .catch(error => {
        console.error('Summary generation error:', error);
        clearInterval(progressInterval);
        summaryProgress.style.display = 'none';
        showStatus('error', 'Error generating summary: ' + error.message);
        summarizeBtn.disabled = false;
    });
}

function updateSummaryProgress(percent) {
    summaryProgressFill.style.width = percent + '%';
    summaryProgressText.textContent = `Analyzing video... ${Math.round(percent)}%`;
}

function displaySummary(data) {
    if (!data || !data.summary || !data.analysis) {
        showStatus('error', 'Invalid summary data received');
        return;
    }
    
    summaryText.innerHTML = `<p>${data.summary.replace(/\n/g, '<br>')}</p>`;
    
    // Hide statistics display
    summaryStats.innerHTML = '';
}

