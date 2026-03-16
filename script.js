// static/js/script.js - UPDATED WITH CHEST X-RAY VALIDATION

// File upload display
document.getElementById('image').addEventListener('change', function(e) {
    const fileName = document.getElementById('file-name');
    const fileUploadArea = document.querySelector('.file-upload-area');
    
    if (this.files.length > 0) {
        const file = this.files[0];
        fileName.textContent = `Selected: ${file.name}`;
        fileName.className = 'mt-2 small fw-bold text-success';
        
        // File preview
        const reader = new FileReader();
        reader.onload = function(e) {
            const existingPreview = fileUploadArea.querySelector('.file-preview');
            if (existingPreview) {
                existingPreview.remove();
            }
            
            const preview = document.createElement('div');
            preview.className = 'file-preview mt-4';
            preview.innerHTML = `
                <div class="preview-container text-center">
                    <img src="${e.target.result}" alt="Preview" class="preview-image rounded shadow-lg" style="max-width: 250px; max-height: 200px;">
                    <p class="small text-muted mt-2 fw-bold">Image Preview</p>
                </div>
            `;
            fileUploadArea.appendChild(preview);
        };
        reader.readAsDataURL(file);
        
    } else {
        fileName.textContent = '';
        const existingPreview = fileUploadArea.querySelector('.file-preview');
        if (existingPreview) {
            existingPreview.remove();
        }
    }
});

// Form submission with PDF generation
document.getElementById('upload-form').addEventListener('submit', function(e) {
    e.preventDefault();
    
    // Validate patient information
    const patientName = document.getElementById('patient_name').value.trim();
    const patientAge = document.getElementById('patient_age').value.trim();
    
    if (!patientName || patientName.length < 2) {
        showError('Please enter a valid patient name (at least 2 characters)');
        return;
    }
    
    if (!patientAge || isNaN(patientAge) || patientAge < 1 || patientAge > 120) {
        showError('Please enter a valid age between 1 and 120');
        return;
    }
    
    const formData = new FormData(this);
    
    // Add patient information to form data
    formData.append('patient_name', patientName);
    formData.append('patient_age', patientAge);
    formData.append('patient_id', document.getElementById('patient_id').value);
    formData.append('patient_gender', document.getElementById('patient_gender').value);
    formData.append('patient_physician', document.getElementById('patient_physician').value);
    
    const resultDiv = document.getElementById('result');
    const loading = document.getElementById('loading');
    const submitBtn = this.querySelector('button[type="submit"]');

    // Loading state
    loading.style.display = 'block';
    resultDiv.style.display = 'none';
    submitBtn.disabled = true;
    submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>AI Analysis & Report Generation...';

    // API call
    fetch('/predict', {
        method: 'POST',
        body: formData
    })
    .then(res => {
        if (!res.ok) {
            throw new Error('Network response was not ok');
        }
        return res.json();
    })
    .then(data => {
        loading.style.display = 'none';
        submitBtn.disabled = false;
        submitBtn.innerHTML = '<i class="fas fa-search me-2"></i>Analyze X-Ray & Generate Report';
        
        // 🩻 CHECK FOR CHEST X-RAY VALIDATION ERROR
        if (data.error === 'NOT_A_CHEST_XRAY') {
            showXRayValidationError(data);
            return;
        }
        
        if (data.error) {
            showError('Error: ' + data.error);
            return;
        }

        // Enhanced result display with PDF download
        const isPneumonia = data.result === 'PNEUMONIA';
        const confidence = parseFloat(data.confidence);
        
        // X-ray validation badge
        const xrayBadge = data.xray_validation ? 
            `<div class="alert alert-info mt-3 mb-0 small py-2">
                <i class="fas fa-check-circle text-success me-2"></i>
                Chest X-ray validated (${data.xray_validation.confidence}% confidence)
                <br><small class="text-muted">${data.xray_validation.reason}</small>
            </div>` : '';
        
        resultDiv.innerHTML = `
            <div class="d-flex align-items-center mb-4">
                <div class="result-icon me-4">
                    <i class="fas ${isPneumonia ? 'fa-exclamation-triangle' : 'fa-check-circle'} fa-3x text-white"></i>
                </div>
                <div class="flex-grow-1">
                    <h2 class="mb-3 ${isPneumonia ? 'text-danger' : 'text-success'} fw-bold">${data.result}</h2>
                    <div class="confidence-meter">
                        <div class="d-flex justify-content-between align-items-center mb-2">
                            <span class="small fw-bold">AI Confidence Level</span>
                            <span class="fw-bold fs-5 ${isPneumonia ? 'text-danger' : 'text-success'}">${data.confidence}%</span>
                        </div>
                        <div class="progress" style="height: 12px; border-radius: 10px; background: rgba(255,255,255,0.3);">
                            <div class="progress-bar ${isPneumonia ? 'bg-danger' : 'bg-success'}" 
                                 role="progressbar" 
                                 style="width: ${confidence}%; border-radius: 10px; transition: width 1s ease;"
                                 aria-valuenow="${confidence}" 
                                 aria-valuemin="0" 
                                 aria-valuemax="100">
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            
            <!-- Patient Info Summary -->
            <div class="patient-summary mb-4 p-3 rounded" style="background: rgba(99, 102, 241, 0.1);">
                <h5 class="mb-2"><i class="fas fa-user me-2"></i>Patient Summary</h5>
                <div class="row small">
                    <div class="col-md-3"><strong>Name:</strong> ${data.patient_info.name}</div>
                    <div class="col-md-2"><strong>Age:</strong> ${data.patient_info.age}</div>
                    <div class="col-md-3"><strong>Gender:</strong> ${data.patient_info.gender}</div>
                    <div class="col-md-4"><strong>Patient ID:</strong> ${data.patient_info.id || 'N/A'}</div>
                </div>
            </div>
            
            ${xrayBadge}
            
            <!-- PDF Download Button -->
            <div class="text-center mt-4">
                <button id="download-pdf" class="btn btn-success btn-lg px-4 py-3">
                    <i class="fas fa-file-pdf me-2"></i>Download Medical Report (PDF)
                </button>
                <p class="small text-muted mt-2">Complete medical report with findings and recommendations</p>
            </div>
            
            ${isPneumonia ? 
                `<div class="alert alert-warning border-0 mt-4">
                    <div class="d-flex align-items-start">
                        <i class="fas fa-info-circle text-warning me-3 fa-lg mt-1"></i>
                        <div>
                            <h5 class="alert-heading mb-2 text-warning fw-bold">🚨 Medical Advisory</h5>
                            <p class="mb-2">This AI analysis suggests possible pneumonia detection. Download the full report and consult with a qualified healthcare professional immediately.</p>
                            <small class="text-muted">Always consult with a doctor for proper diagnosis and treatment recommendations.</small>
                        </div>
                    </div>
                </div>` : 
                `<div class="alert alert-info border-0 mt-4">
                    <div class="d-flex align-items-start">
                        <i class="fas fa-check-circle text-info me-3 fa-lg mt-1"></i>
                        <div>
                            <h5 class="alert-heading mb-2 text-info fw-bold">✅ No Pneumonia Detected</h5>
                            <p class="mb-2">The AI analysis shows no signs of pneumonia in the X-ray image. Download the complete report for detailed findings.</p>
                            <small class="text-muted">For any health concerns or symptoms, please consult with a healthcare professional.</small>
                        </div>
                    </div>
                </div>`
            }
        `;
        
        resultDiv.className = isPneumonia ? 'alert alert-danger' : 'alert alert-success';
        resultDiv.style.display = 'block';
        
        // PDF download button event
        document.getElementById('download-pdf').addEventListener('click', function() {
            window.open(`/download-report/${data.pdf_path}`, '_blank');
        });
        
        // Scroll to result
        setTimeout(() => {
            resultDiv.scrollIntoView({ behavior: 'smooth', block: 'center' });
        }, 500);
    })
    .catch(err => {
        loading.style.display = 'none';
        submitBtn.disabled = false;
        submitBtn.innerHTML = '<i class="fas fa-search me-2"></i>Analyze X-Ray & Generate Report';
        showError('Analysis failed. Please check your connection and try again. ' + err.message);
        console.error('Prediction error:', err);
    });
});

// 🩻 SPECIAL FUNCTION FOR X-RAY VALIDATION ERROR
function showXRayValidationError(data) {
    const resultDiv = document.getElementById('result');
    
    resultDiv.innerHTML = `
        <div class="alert alert-warning border-0">
            <div class="d-flex align-items-start">
                <div class="me-3">
                    <i class="fas fa-x-ray fa-3x text-warning"></i>
                </div>
                <div>
                    <h4 class="text-warning mb-2 fw-bold">⚠️ Not a Chest X-Ray</h4>
                    <p class="mb-3">${data.message}</p>
                    
                    <div class="alert alert-light mb-3 p-3">
                        <h5 class="mb-2 small fw-bold">📊 Analysis Details:</h5>
                        <ul class="small mb-0">
                            <li><strong>Confidence:</strong> ${data.confidence}% not a chest X-ray</li>
                            <li><strong>Reason:</strong> ${data.reason || 'Image features not matching typical X-ray patterns'}</li>
                        </ul>
                    </div>
                    
                    <div class="alert alert-info p-3">
                        <h5 class="mb-2 small fw-bold">💡 Suggestion:</h5>
                        <p class="mb-0 small">${data.suggestion || 'Please upload a frontal chest X-ray image for accurate pneumonia detection.'}</p>
                    </div>
                    
                    <button onclick="resetUpload()" class="btn btn-primary mt-3">
                        <i class="fas fa-upload me-2"></i>Upload Different Image
                    </button>
                </div>
            </div>
        </div>
    `;
    
    resultDiv.className = 'alert';
    resultDiv.style.display = 'block';
    resultDiv.scrollIntoView({ behavior: 'smooth', block: 'center' });
}

// Reset function
function resetUpload() {
    document.getElementById('image').value = '';
    document.getElementById('file-name').textContent = '';
    const fileUploadArea = document.querySelector('.file-upload-area');
    const preview = fileUploadArea.querySelector('.file-preview');
    if (preview) preview.remove();
    document.getElementById('result').style.display = 'none';
}

// Error display function
function showError(message) {
    const resultDiv = document.getElementById('result');
    resultDiv.innerHTML = `
        <div class="alert alert-danger border-0">
            <div class="d-flex align-items-center">
                <div class="me-3">
                    <i class="fas fa-exclamation-circle fa-3x text-danger"></i>
                </div>
                <div>
                    <h4 class="text-danger mb-2 fw-bold">⚠️ Analysis Error</h4>
                    <p class="mb-0">${message}</p>
                </div>
            </div>
        </div>
    `;
    resultDiv.style.display = 'block';
    
    setTimeout(() => {
        resultDiv.scrollIntoView({ behavior: 'smooth', block: 'center' });
    }, 300);
}

// Smooth scrolling for navigation
document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function (e) {
        e.preventDefault();
        const target = document.querySelector(this.getAttribute('href'));
        if (target) {
            target.scrollIntoView({ behavior: 'smooth', block: 'start' });
        }
    });
});

// Navbar background on scroll
window.addEventListener('scroll', function() {
    const navbar = document.querySelector('.navbar');
    if (window.scrollY > 50) {
        navbar.classList.add('navbar-scrolled');
    } else {
        navbar.classList.remove('navbar-scrolled');
    }
});

console.log('🚀 PneumoScan AI Frontend Loaded Successfully!');