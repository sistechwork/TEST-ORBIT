class ProctorMonitor {
    constructor() {
        this.videoStream = null;
        this.audioStream = null;
        this.audioContext = null;
        this.analyser = null;
        this.faceDetection = null;
        this.monitoringActive = false;
        
        this.violations = {
            noFace: 0,
            multipleFaces: 0,
            highNoise: 0
        };
        
        this.lastLoggedViolations = {
            no_face_detected: 0,
            multiple_faces: 0,
            high_noise_level: 0
        };
        
        this.violationCooldown = 10000;
        this.warningThreshold = 3;
        this.lastFaceDetectionTime = Date.now();
        this.lastNoiseCheckTime = Date.now();
        this.currentFaceStatus = null;
        this.faceAbsentSince = null;
        this.faceAbsentWarningThreshold = 1000;
    }
    
    async initialize() {
        try {
            await this.initializeCamera();
            await this.initializeAudio();
            await this.initializeFaceDetection();
            this.startMonitoring();
            console.log('Proctoring system initialized successfully');
            return true;
        } catch (error) {
            console.error('Failed to initialize proctoring:', error);
            this.showError('Failed to initialize monitoring system: ' + error.message);
            return false;
        }
    }
    
    async initializeCamera() {
        this.videoStream = await navigator.mediaDevices.getUserMedia({ 
            video: { facingMode: 'user' },
            audio: false
        });
        
        const video = document.getElementById('proctorVideo');
        if (video) {
            video.srcObject = this.videoStream;
        }
    }
    
    async initializeAudio() {
        this.audioStream = await navigator.mediaDevices.getUserMedia({ 
            video: false,
            audio: true
        });
        
        this.audioContext = new (window.AudioContext || window.webkitAudioContext)();
        this.analyser = this.audioContext.createAnalyser();
        const source = this.audioContext.createMediaStreamSource(this.audioStream);
        source.connect(this.analyser);
        
        this.analyser.fftSize = 256;
        this.analyser.smoothingTimeConstant = 0.8;
    }
    
    async initializeFaceDetection() {
        this.faceDetection = new FaceDetection({locateFile: (file) => {
            return `https://cdn.jsdelivr.net/npm/@mediapipe/face_detection/${file}`;
        }});
        
        this.faceDetection.setOptions({
            model: 'short',
            minDetectionConfidence: 0.5
        });
        
        this.faceDetection.onResults((results) => this.handleFaceDetectionResults(results));
    }
    
    startMonitoring() {
        this.monitoringActive = true;
        this.startFaceDetectionLoop();
        this.startAudioMonitoring();
    }
    
    startFaceDetectionLoop() {
        const video = document.getElementById('proctorVideo');
        if (!video || !this.monitoringActive) return;
        
        const detectFace = async () => {
            if (!this.monitoringActive) return;
            
            const now = Date.now();
            if (now - this.lastFaceDetectionTime >= 1000) {
                this.lastFaceDetectionTime = now;
                
                try {
                    await this.faceDetection.send({image: video});
                } catch (error) {
                    console.error('Face detection error:', error);
                }
            }
            
            requestAnimationFrame(detectFace);
        };
        
        detectFace();
    }
    
    handleFaceDetectionResults(results) {
        const faceCount = results.detections ? results.detections.length : 0;
        const now = Date.now();
        
        if (faceCount === 0) {
            if (this.faceAbsentSince === null) {
                this.faceAbsentSince = now;
            }
            
            const absenceDuration = now - this.faceAbsentSince;
            
            if (absenceDuration > this.faceAbsentWarningThreshold && this.currentFaceStatus !== 'no_face') {
                this.currentFaceStatus = 'no_face';
                this.violations.noFace++;
                this.showWarning('No face detected! Please position yourself in front of the camera.', 'error');
                this.logViolationWithCooldown('no_face_detected', `No face visible for ${Math.round(absenceDuration/1000)}s`, 'error');
            }
        } else if (faceCount > 1 && this.currentFaceStatus !== 'multiple_faces') {
            this.faceAbsentSince = null;
            this.currentFaceStatus = 'multiple_faces';
            this.violations.multipleFaces++;
            this.showWarning('Multiple faces detected! Only you should be visible.', 'error');
            this.logViolationWithCooldown('multiple_faces', `${faceCount} faces detected`, 'error');
        } else if (faceCount === 1) {
            this.faceAbsentSince = null;
            if (this.currentFaceStatus !== 'ok') {
                this.currentFaceStatus = 'ok';
                this.hideWarning('face');
            }
        }
    }
    
    startAudioMonitoring() {
        const checkAudio = () => {
            if (!this.monitoringActive) return;
            
            const now = Date.now();
            if (now - this.lastNoiseCheckTime >= 3000) {
                this.lastNoiseCheckTime = now;
                
                const bufferLength = this.analyser.frequencyBinCount;
                const dataArray = new Uint8Array(bufferLength);
                this.analyser.getByteTimeDomainData(dataArray);
                
                let sum = 0;
                for (let i = 0; i < bufferLength; i++) {
                    const normalized = (dataArray[i] - 128) / 128;
                    sum += normalized * normalized;
                }
                const rms = Math.sqrt(sum / bufferLength);
                const energyLevel = Math.round(rms * 100);
                
                if (energyLevel > 15) {
                    this.violations.highNoise++;
                    this.showWarning('High background noise detected! Please maintain silence.', 'warning');
                    this.logViolationWithCooldown('high_noise_level', `Energy level: ${energyLevel}%`, 'warning');
                } else if (energyLevel > 8) {
                    this.showWarning('Background noise detected. Please minimize noise.', 'info');
                }
            }
            
            setTimeout(checkAudio, 1000);
        };
        
        checkAudio();
    }
    
    showWarning(message, level = 'warning') {
        const warningBox = document.getElementById('proctorWarning');
        if (!warningBox) return;
        
        warningBox.textContent = message;
        warningBox.className = 'proctor-warning ' + level;
        warningBox.style.display = 'block';
        
        if (level === 'info') {
            setTimeout(() => {
                warningBox.style.display = 'none';
            }, 3000);
        }
    }
    
    hideWarning(type) {
        const warningBox = document.getElementById('proctorWarning');
        if (warningBox) {
            warningBox.style.display = 'none';
        }
    }
    
    showError(message) {
        alert(message);
    }
    
    async logViolationWithCooldown(eventType, details, severity = 'warning') {
        const now = Date.now();
        const lastLogged = this.lastLoggedViolations[eventType];
        
        if (lastLogged && (now - lastLogged) < this.violationCooldown) {
            return;
        }
        
        this.lastLoggedViolations[eventType] = now;
        
        try {
            const response = await fetch('/proctor/events', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    event_type: eventType,
                    event_details: details,
                    severity: severity
                })
            });
            
            if (response.status === 429) {
                console.log('Rate limited, slowing down violation logging');
            }
        } catch (error) {
            console.error('Failed to log violation:', error);
        }
    }
    
    stop() {
        this.monitoringActive = false;
        
        if (this.videoStream) {
            this.videoStream.getTracks().forEach(track => track.stop());
        }
        if (this.audioStream) {
            this.audioStream.getTracks().forEach(track => track.stop());
        }
        if (this.audioContext) {
            this.audioContext.close();
        }
        if (this.faceDetection) {
            this.faceDetection.close();
        }
    }
}

let proctorMonitor = null;

window.addEventListener('load', async () => {
    const proctorVideo = document.getElementById('proctorVideo');
    if (proctorVideo) {
        proctorMonitor = new ProctorMonitor();
        const initialized = await proctorMonitor.initialize();
        
        if (!initialized) {
            console.error('Proctoring system failed to initialize');
        }
    }
});

window.addEventListener('beforeunload', () => {
    if (proctorMonitor) {
        proctorMonitor.stop();
    }
});
