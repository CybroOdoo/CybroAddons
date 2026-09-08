document.addEventListener('DOMContentLoaded', function () {
    // ----------------------------------------------------
    // State Variables
    // ----------------------------------------------------
    let signatureMode = 'draw'; // 'draw', 'type', or 'upload'
    let inkColor = '#000000';
    let isDrawing = false;
    let hasDrawn = false;
    let uploadedBase64 = null;
    let selectedFont = 'Caveat';

    // ----------------------------------------------------
    // Element Selectors
    // ----------------------------------------------------
    const canvas = document.getElementById('signature-pad');
    const clearBtn = document.getElementById('clear-canvas');
    const colorBlackBtn = document.getElementById('color-black');
    const colorBlueBtn = document.getElementById('color-blue');
    
    const typedInput = document.getElementById('typed-name');
    const fontCards = document.querySelectorAll('.font-select-card');
    
    const fileInput = document.getElementById('upload-signature-file');
    const uploadPreviewContainer = document.getElementById('upload-preview-container');
    const uploadPreview = document.getElementById('upload-preview');
    
    const consentCheck = document.getElementById('consent-check');
    const submitBtn = document.getElementById('submit-signature');
    const errorAlert = document.getElementById('error-alert');
    const tokenInput = document.getElementById('access_token');
    
    const tabs = document.querySelectorAll('#signatureTabs button');

    // ----------------------------------------------------
    // Canvas Initialization & Drawing Logic
    // ----------------------------------------------------
    let ctx = null;
    if (canvas) {
        ctx = canvas.getContext('2d');
        resizeCanvas();
        window.addEventListener('resize', resizeCanvas);
        setupCanvasListeners();
    }

    function resizeCanvas() {
        if (!canvas) return;
        // Save current contents if drawn
        const tempImage = canvas.toDataURL();
        
        // Resize canvas elements coordinates
        const rect = canvas.getBoundingClientRect();
        canvas.width = rect.width;
        canvas.height = rect.height;
        
        // Restore styling context
        ctx.strokeStyle = inkColor;
        ctx.lineWidth = 2.5;
        ctx.lineCap = 'round';
        ctx.lineJoin = 'round';
        
        // Restore image
        if (hasDrawn) {
            const img = new Image();
            img.src = tempImage;
            img.onload = function() {
                ctx.drawImage(img, 0, 0);
            };
        }
    }

    function setupCanvasListeners() {
        // Mouse Events
        canvas.addEventListener('mousedown', startDrawing);
        canvas.addEventListener('mousemove', draw);
        canvas.addEventListener('mouseup', stopDrawing);
        canvas.addEventListener('mouseleave', stopDrawing);

        // Touch Events (for mobile tablets/phones)
        canvas.addEventListener('touchstart', startDrawingTouch);
        canvas.addEventListener('touchmove', drawTouch);
        canvas.addEventListener('touchend', stopDrawing);
    }

    function getMousePos(e) {
        const rect = canvas.getBoundingClientRect();
        return {
            x: e.clientX - rect.left,
            y: e.clientY - rect.top
        };
    }

    function getTouchPos(e) {
        const rect = canvas.getBoundingClientRect();
        const touch = e.touches[0];
        return {
            x: touch.clientX - rect.left,
            y: touch.clientY - rect.top
        };
    }

    function startDrawing(e) {
        isDrawing = true;
        hasDrawn = true;
        const pos = getMousePos(e);
        ctx.beginPath();
        ctx.moveTo(pos.x, pos.y);
        validateInputs();
    }

    function draw(e) {
        if (!isDrawing) return;
        const pos = getMousePos(e);
        ctx.lineTo(pos.x, pos.y);
        ctx.stroke();
    }

    function startDrawingTouch(e) {
        isDrawing = true;
        hasDrawn = true;
        const pos = getTouchPos(e);
        ctx.beginPath();
        ctx.moveTo(pos.x, pos.y);
        e.preventDefault();
        validateInputs();
    }

    function drawTouch(e) {
        if (!isDrawing) return;
        const pos = getTouchPos(e);
        ctx.lineTo(pos.x, pos.y);
        ctx.stroke();
        e.preventDefault();
    }

    function stopDrawing() {
        isDrawing = false;
        validateInputs();
    }

    if (clearBtn) {
        clearBtn.addEventListener('click', function() {
            if (!canvas) return;
            ctx.clearRect(0, 0, canvas.width, canvas.height);
            hasDrawn = false;
            validateInputs();
        });
    }

    if (colorBlackBtn && colorBlueBtn) {
        colorBlackBtn.addEventListener('click', function() {
            inkColor = '#000000';
            ctx.strokeStyle = inkColor;
            colorBlackBtn.classList.add('active');
            colorBlueBtn.classList.remove('active');
        });
        colorBlueBtn.addEventListener('click', function() {
            inkColor = '#0000FF';
            ctx.strokeStyle = inkColor;
            colorBlueBtn.classList.add('active');
            colorBlackBtn.classList.remove('active');
        });
    }

    // ----------------------------------------------------
    // Tab Change & Input Selectors
    // ----------------------------------------------------
    tabs.forEach(tab => {
        tab.addEventListener('shown.bs.tab', function (e) {
            const targetId = e.target.getAttribute('data-bs-target');
            if (targetId === '#draw-pane') {
                signatureMode = 'draw';
                resizeCanvas();
            } else if (targetId === '#type-pane') {
                signatureMode = 'type';
            } else if (targetId === '#upload-pane') {
                signatureMode = 'upload';
            }
            validateInputs();
        });
    });

    // ----------------------------------------------------
    // Typed Signature Flow
    // ----------------------------------------------------
    if (typedInput) {
        typedInput.addEventListener('input', function() {
            const val = this.value || 'Your Name';
            document.querySelectorAll('.font-select-card .preview-text').forEach(el => {
                el.textContent = val;
            });
            validateInputs();
        });
    }

    fontCards.forEach(card => {
        card.addEventListener('click', function() {
            fontCards.forEach(c => c.classList.remove('active'));
            this.classList.add('active');
            selectedFont = this.getAttribute('data-font');
        });
    });

    // Render text to canvas to generate a signature image from typed text
    function getTypedSignatureImage() {
        const text = typedInput.value || '';
        const tempCanvas = document.createElement('canvas');
        tempCanvas.width = 400;
        tempCanvas.height = 150;
        const tempCtx = tempCanvas.getContext('2d');
        
        tempCtx.clearRect(0, 0, tempCanvas.width, tempCanvas.height);
        
        // Select ink color matching draw pane selection
        tempCtx.fillStyle = inkColor;
        
        // Font definition mapping
        let fontStyle = '';
        if (selectedFont === 'Caveat') {
            fontStyle = "bold italic 44px 'Caveat', cursive";
        } else if (selectedFont === 'Pacifico') {
            fontStyle = "28px 'Pacifico', cursive";
        } else {
            fontStyle = "32px sans-serif";
        }
        
        tempCtx.font = fontStyle;
        tempCtx.textAlign = 'center';
        tempCtx.textBaseline = 'middle';
        
        // Draw centered signature name
        tempCtx.fillText(text, tempCanvas.width / 2, tempCanvas.height / 2);
        
        return tempCanvas.toDataURL('image/png');
    }

    // ----------------------------------------------------
    // Upload Signature Flow
    // ----------------------------------------------------
    if (fileInput) {
        fileInput.addEventListener('change', function(e) {
            const file = e.target.files[0];
            if (!file) {
                uploadedBase64 = null;
                uploadPreviewContainer.classList.add('d-none');
                validateInputs();
                return;
            }

            // Size Check (< 2MB)
            if (file.size > 2 * 1024 * 1024) {
                alert("The selected file is too large. Max size is 2MB.");
                fileInput.value = '';
                uploadedBase64 = null;
                uploadPreviewContainer.classList.add('d-none');
                validateInputs();
                return;
            }

            const reader = new FileReader();
            reader.onload = function(evt) {
                uploadedBase64 = evt.target.result;
                uploadPreview.src = uploadedBase64;
                uploadPreviewContainer.classList.remove('d-none');
                validateInputs();
            };
            reader.readAsDataURL(file);
        });
    }

    // ----------------------------------------------------
    // Validation
    // ----------------------------------------------------
    if (consentCheck) {
        consentCheck.addEventListener('change', validateInputs);
    }

    function validateInputs() {
        if (!consentCheck || !submitBtn) return;
        
        const isConsentChecked = consentCheck.checked;
        let isSignatureProvided = false;

        if (signatureMode === 'draw') {
            isSignatureProvided = hasDrawn;
        } else if (signatureMode === 'type') {
            isSignatureProvided = typedInput && typedInput.value.trim().length > 0;
        } else if (signatureMode === 'upload') {
            isSignatureProvided = !!uploadedBase64;
        }

        if (isConsentChecked && isSignatureProvided) {
            submitBtn.classList.remove('disabled');
            submitBtn.removeAttribute('disabled');
        } else {
            submitBtn.classList.add('disabled');
            submitBtn.setAttribute('disabled', 'disabled');
        }
    }

    // ----------------------------------------------------
    // AJAX Submission
    // ----------------------------------------------------
    if (submitBtn) {
        submitBtn.addEventListener('click', submitSignature);
    }

    function submitSignature() {
        if (submitBtn.classList.contains('disabled')) return;

        // Visual feedback
        submitBtn.classList.add('disabled');
        submitBtn.setAttribute('disabled', 'disabled');
        submitBtn.textContent = 'Submitting signature...';
        if (errorAlert) errorAlert.classList.add('d-none');

        let signatureData = '';
        if (signatureMode === 'draw') {
            signatureData = canvas.toDataURL('image/png');
        } else if (signatureMode === 'type') {
            signatureData = getTypedSignatureImage();
        } else if (signatureMode === 'upload') {
            signatureData = uploadedBase64;
        }

        const token = tokenInput.value;

        // Odoo Controllers JSON-RPC format expects params wrap
        fetch('/wm_signature/sign/submit', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                params: {
                    token: token,
                    signature: signatureData
                }
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                showError(data.error.message || 'An error occurred during submission.');
            } else if (data.result && data.result.success) {
                window.location.href = data.result.redirect_url;
            } else {
                showError((data.result && data.result.error) || 'Submission failed.');
            }
        })
        .catch(err => {
            showError('Network error. Please try again.');
            console.error(err);
        });
    }

    function showError(msg) {
        if (errorAlert) {
            errorAlert.textContent = msg;
            errorAlert.classList.remove('d-none');
        }
        
        // Reset button
        submitBtn.classList.remove('disabled');
        submitBtn.removeAttribute('disabled');
        submitBtn.textContent = 'Sign Document';
    }
});
