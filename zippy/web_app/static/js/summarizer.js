// Video Summarizer JavaScript

let summarizeUploadedVideoPath = null;

// Upload Area Setup
const summarizeUploadArea = document.getElementById('summarizeUploadArea');
const summarizeVideoInput = document.getElementById('summarizeVideoInput');
const summarizeUploadStatus = document.getElementById('summarizeUploadStatus');
const summarizeStatusMessage = document.getElementById('summarizeStatusMessage');
const analyzeStep = document.getElementById('analyzeStep');
const analyzeBtn = document.getElementById('analyzeBtn');
const analyzeProgress = document.getElementById('analyzeProgress');
const analyzeProgressFill = document.getElementById('analyzeProgressFill');
const summaryStep = document.getElementById('summaryStep');
const summaryText = document.getElementById('summaryText');
const summaryStats = document.getElementById('summaryStats');
const downloadReportBtn = document.getElementById('downloadReportBtn');

// Drag and drop handlers
summarizeUploadArea.addEventListener('dragover', (e) => {
    e.preventDefault();
    summarizeUploadArea.classList.add('dragover');
});

summarizeUploadArea.addEventListener('dragleave', () => {
    summarizeUploadArea.classList.remove('dragover');
});

summarizeUploadArea.addEventListener('drop', (e) => {
    e.preventDefault();
    summarizeUploadArea.classList.remove('dragover');
    const files = e.dataTransfer.files;
    if (files.length > 0) {
        handleSummarizeUpload(files[0]);
    }
});

summarizeUploadArea.addEventListener('click', () => {
    summarizeVideoInput.click();
});

summarizeVideoInput.addEventListener('change', (e) => {
    if (e.target.files.length > 0) {
        handleSummarizeUpload(e.target.files[0]);
    }
});

function handleSummarizeUpload(file) {
    // Validate file
    const validTypes = ['video/mp4', 'video/avi', 'video/quicktime', 'video/x-msvideo'];
    if (!validTypes.some(type => file.type.includes(type)) && !file.name.match(/\.(mp4|avi|mov|mkv)$/i)) {
        showSummarizeStatus('error', 'Invalid file type. Please upload MP4, AVI, MOV, or MKV.');
        return;
    }

    if (file.size > 500 * 1024 * 1024) {
        showSummarizeStatus('error', 'File size exceeds 500MB limit.');
        return;
    }

    // Store file reference
    summarizeUploadedVideoPath = file;
    
    showSummarizeStatus('success', `Video uploaded: ${file.name}`);
    analyzeStep.style.display = 'block';
}

function showSummarizeStatus(type, message) {
    summarizeUploadStatus.style.display = 'block';
    summarizeStatusMessage.textContent = message;
    summarizeStatusMessage.className = `status-message ${type}`;
}

analyzeBtn.addEventListener('click', () => {
    if (!summarizeUploadedVideoPath) {
        showSummarizeStatus('error', 'Please upload a video first.');
        return;
    }
    
    analyzeVideo();
});

function analyzeVideo() {
    analyzeBtn.disabled = true;
    analyzeProgress.style.display = 'block';
    summaryStep.style.display = 'none';
    
    const formData = new FormData();
    formData.append('video', summarizeUploadedVideoPath);
    
    // Simulate progress
    let progress = 0;
    const progressInterval = setInterval(() => {
        if (progress < 90) {
            progress += Math.random() * 25;
            if (progress > 90) progress = 90;
            updateAnalyzeProgress(progress);
        }
    }, 400);
    
    fetch('/api/summarize-video', {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        clearInterval(progressInterval);
        updateAnalyzeProgress(100);
        
        if (data.success) {
            showSummarizeStatus('success', 'Video analysis completed!');
            displaySummary(data);
            summaryStep.style.display = 'block';
        } else {
            showSummarizeStatus('error', data.error || 'Analysis failed');
        }
        
        analyzeBtn.disabled = false;
    })
    .catch(error => {
        clearInterval(progressInterval);
        showSummarizeStatus('error', 'Error: ' + error.message);
        analyzeBtn.disabled = false;
    });
}

function updateAnalyzeProgress(percent) {
    analyzeProgressFill.style.width = percent + '%';
    analyzeProgressFill.textContent = Math.round(percent) + '%';
}

function displaySummary(data) {
    // Display text summary
    summaryText.innerHTML = `<p>${data.summary.replace(/\n/g, '<br>')}</p>`;
    
    // Hide stats display
    summaryStats.innerHTML = '';
    
    // Show download report button
    downloadReportBtn.style.display = 'inline-block';
    downloadReportBtn.addEventListener('click', () => {
        downloadReport(data);
    });
}

function downloadReport(data) {
    const reportContent = `
Video Summary Report
=====================
Generated: ${new Date().toLocaleString()}

ANALYSIS SUMMARY:
-----------------
${data.summary}

STATISTICS:
-----------
Duration: ${data.stats.duration.toFixed(2)} seconds
Total Frames: ${data.stats.total_frames}
FPS: ${data.stats.fps.toFixed(2)}
Trajectory Points: ${data.stats.trajectory_points}
Total Distance Traveled: ${data.stats.total_distance.toFixed(0)} pixels
Movement Pattern: ${data.stats.movement_pattern}

---
Generated by Bag Detection & Tracking System
    `;
    
    const element = document.createElement('a');
    element.setAttribute('href', 'data:text/plain;charset=utf-8,' + encodeURIComponent(reportContent));
    element.setAttribute('download', `report_${new Date().getTime()}.txt`);
    element.style.display = 'none';
    document.body.appendChild(element);
    element.click();
    document.body.removeChild(element);
}
