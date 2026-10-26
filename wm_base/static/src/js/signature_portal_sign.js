// Signing portal page logic. Page data is read from #wm-sign-config.
window.bootstrap = window.bootstrap || {Modal: window.Modal, Tab: window.Tab};
(function () {
                const config = document.getElementById('wm-sign-config').dataset;
                const token = config.token;
                const signerRoleId = parseInt(config.signerRoleId, 10) || 0;
                let templateItems = JSON.parse(config.templateItems);
                const filledValues = JSON.parse(config.filledValues);
                const activeRoleIds = JSON.parse(config.activeRoleIds);

                // Values typed by other signers are untrusted: escape them
                // before putting them into innerHTML.
                function escapeHtml(value) {
                    return String(value ?? '').replace(/[&<>"']/g, c => ({
                        '&': '&amp;', '<': '<', '>': '>', '"': '&quot;', "'": '&#39;',
                    })[c]);
                }

                function isFieldInteractive(item) {
                    return item.role_id === signerRoleId || !activeRoleIds.includes(item.role_id) || activeRoleIds.length === 1;
                }

                let fieldsState = {}; // maps item_id to { value, signature }
                let currentTargetField = null;

                // Load existing filled values into fieldsState
                for (const itemId in filledValues) {
                    fieldsState[itemId] = {
                        value: filledValues[itemId].value,
                        signature: filledValues[itemId].signature_image ? 'data:image/png;base64,' + filledValues[itemId].signature_image : '',
                        filledByOthers: true
                    };
                }

                // --- PDF LOADING ---
                const pdfUrl = `/wm_signature/request/pdf/${token}`;
                const pdfSignCanvas = document.getElementById('pdf-sign-canvas');
                const pdfSignOverlay = document.getElementById('pdf-sign-overlay');

                async function renderSigningPdf() {
                    const lib = window.pdfjsLib || window['pdfjs-dist/build/pdf'] || (typeof globalThis !== 'undefined' && globalThis['pdfjs-dist/build/pdf']);
                    if (!pdfSignCanvas || !pdfSignOverlay || !lib) {
                        console.error('PDF library or canvas not available:', { pdfSignCanvas, pdfSignOverlay, lib });
                        return;
                    }

                    lib.GlobalWorkerOptions.workerSrc = '/wm_base/static/src/vendor/pdf.worker.min.js';

                    try {
                        const res = await fetch(pdfUrl, { credentials: 'same-origin' });
                        if (!res.ok) throw new Error('HTTP ' + res.status + ' ' + res.statusText);
                        const buffer = await res.arrayBuffer();
                        const loadingTask = lib.getDocument({ data: buffer });
                        const pdf = await loadingTask.promise;
                        const page = await pdf.getPage(1);
                        const desiredWidth = 850;
                        const initialViewport = page.getViewport({ scale: 1 });
                        const scale = desiredWidth / initialViewport.width;
                        const viewport = page.getViewport({ scale });
                        const context = pdfSignCanvas.getContext('2d');

                        pdfSignCanvas.width = viewport.width;
                        pdfSignCanvas.height = viewport.height;
                        pdfSignCanvas.style.width = `${viewport.width}px`;
                        pdfSignCanvas.style.height = `${viewport.height}px`;
                        pdfSignOverlay.style.width = `${viewport.width}px`;
                        pdfSignOverlay.style.height = `${viewport.height}px`;
                        pdfSignOverlay.innerHTML = '';

                        await page.render({
                            canvasContext: context,
                            viewport: viewport,
                        }).promise;

                        // Fallback: If no signature fields were pre-designed on template, auto-create signature field at bottom
                        if (!templateItems || templateItems.length === 0) {
                            templateItems = [
                                {
                                    id: 999901,
                                    page: 1,
                                    x: 8,
                                    y: 80,
                                    width: 38,
                                    height: 9,
                                    type: 'signature',
                                    role_id: signerRoleId
                                }
                            ];
                        }
                        // Enable overlay for click interaction
                        pdfSignOverlay.style.pointerEvents = 'all';
                        // Render all template items on overlay
                        templateItems.forEach(item => {
                            renderItemBox(item, pdfSignOverlay);
                        });
                    } catch (error) {
                        console.error('Failed to render PDF in signing portal:', error);
                        pdfSignOverlay.style.pointerEvents = 'all';
                        pdfSignOverlay.innerHTML = `
                            <div style="position:absolute;inset:0;display:flex;align-items:center;justify-content:center;color:#fff;background:#333;padding:24px;text-align:center;">
                                <div>
                                    <div style="font-size:18px;font-weight:600;margin-bottom:8px;">Unable to load document preview</div>
                                    <a href="${pdfUrl}" target="_blank" style="color:#8ec5ff;text-decoration:underline;">Open PDF in a new tab</a>
                                </div>
                            </div>
                        `;
                    }
                }
                renderSigningPdf();

                function renderItemBox(item, overlay) {
                    const box = document.createElement('div');
                    box.className = 'field-box';
                    box.dataset.id = item.id;
                    box.style.left = item.x + '%';
                    box.style.top = item.y + '%';
                    box.style.width = item.width + '%';
                    box.style.height = item.height + '%';
                    
                    const isInteractive = isFieldInteractive(item);
                    if (isInteractive) {
                        box.classList.add('interactive');
                    }

                    // Display status
                    const state = fieldsState[item.id];
                    if (state) {
                        box.classList.add('filled');
                        if (item.type === 'signature') {
                            if (state.signature) {
                                box.innerHTML = `<img src="${escapeHtml(state.signature)}"/>`;
                            } else {
                                box.innerHTML = `<span class="small">Signed</span>`;
                            }
                        } else {
                            box.innerHTML = `<span class="text-truncate px-1">${escapeHtml(state.value)}</span>`;
                        }
                    } else {
                        const isSig = item.type === 'signature';
                        const actionLabel = isSig ? 'Click to Sign' : `Click to fill ${item.type}`;
                        const label = isSig ? 'Signature' : (item.type.charAt(0).toUpperCase() + item.type.slice(1));
                        box.innerHTML = `<span class="small">${isInteractive ? actionLabel : label}</span>`;
                    }

                    overlay.appendChild(box);

                    if (isInteractive) {
                        box.addEventListener('click', function() {
                            handleFieldClick(item, box);
                        });
                    }
                }

                function handleFieldClick(item, box) {
                    currentTargetField = { item, box };
                    
                    if (item.type === 'signature') {
                        // Open signature modal
                        const modalTitle = document.getElementById('signatureModalLabel');
                        if (modalTitle) {
                            modalTitle.textContent = 'Adopt Your Signature';
                        }
                        const typeLabel = document.querySelector('label[for="typed-name"]');
                        if (typeLabel) {
                            typeLabel.textContent = 'Enter your full name';
                        }
                        const typedInput = document.getElementById('typed-name');
                        if (typedInput) {
                            typedInput.placeholder = 'Type signature...';
                            typedInput.value = config.partnerName;
                            document.querySelectorAll('.font-select-card .preview-text').forEach(el => {
                                el.textContent = typedInput.value;
                            });
                        }
                        const adoptBtn = document.getElementById('adopt-signature-btn');
                        if (adoptBtn) {
                            adoptBtn.innerHTML = '<i class="fa fa-check me-1"></i> Adopt & Sign';
                        }
                        const modal = new bootstrap.Modal(document.getElementById('signatureModal'));
                        modal.show();
                        // Reset pads and drawings
                        setTimeout(resizeCanvas, 300);
                    } else {
                        // Open inline text modal
                        const modal = new bootstrap.Modal(document.getElementById('textInputModal'));
                        const input = document.getElementById('inline-text-input');
                        input.value = fieldsState[item.id] ? fieldsState[item.id].value : '';
                        
                        // If auto-fill applies
                        if (!input.value) {
                            if (item.type === 'name') input.value = config.partnerName;
                            else if (item.type === 'email') input.value = config.partnerEmail;
                            else if (item.type === 'phone') input.value = config.partnerPhone;
                            else if (item.type === 'company') input.value = config.partnerCompany;
                            else if (item.type === 'date') input.value = new Date().toISOString().split('T')[0];
                        }
                        
                        modal.show();
                    }
                }

                // Inline Text Save
                document.getElementById('save-inline-text').addEventListener('click', function() {
                    if (!currentTargetField) return;
                    const value = document.getElementById('inline-text-input').value;
                    const { item, box } = currentTargetField;
                    
                    fieldsState[item.id] = { value: value, signature: '' };
                    
                    box.classList.add('filled');
                    box.innerHTML = `<span class="text-truncate px-1">${escapeHtml(value)}</span>`;
                    
                    bootstrap.Modal.getInstance(document.getElementById('textInputModal')).hide();
                    validateCompletion();
                });

                // Signature Canvas Pad drawing
                let signatureMode = 'draw';
                let inkColor = '#000000';
                let isDrawing = false;
                let hasDrawn = false;
                let uploadedBase64 = null;
                let selectedFont = 'Caveat';

                const canvas = document.getElementById('signature-pad');
                const ctx = canvas ? canvas.getContext('2d') : null;

                function resizeCanvas() {
                    if (!canvas) return;
                    const rect = canvas.getBoundingClientRect();
                    canvas.width = rect.width;
                    canvas.height = rect.height;
                    
                    ctx.strokeStyle = inkColor;
                    ctx.lineWidth = 2.5;
                    ctx.lineCap = 'round';
                    ctx.lineJoin = 'round';
                }

                if (canvas) {
                    canvas.addEventListener('mousedown', e => {
                        isDrawing = true;
                        hasDrawn = true;
                        const rect = canvas.getBoundingClientRect();
                        ctx.beginPath();
                        ctx.moveTo(e.clientX - rect.left, e.clientY - rect.top);
                        validateModalInputs();
                    });
                    
                    canvas.addEventListener('mousemove', e => {
                        if (!isDrawing) return;
                        const rect = canvas.getBoundingClientRect();
                        ctx.lineTo(e.clientX - rect.left, e.clientY - rect.top);
                        ctx.stroke();
                    });
                    
                    canvas.addEventListener('mouseup', () => isDrawing = false);
                    canvas.addEventListener('mouseleave', () => isDrawing = false);

                    // Touch support for mobile and tablets
                    canvas.addEventListener('touchstart', e => {
                        if (e.touches.length > 0) {
                            const touch = e.touches[0];
                            const rect = canvas.getBoundingClientRect();
                            isDrawing = true;
                            hasDrawn = true;
                            ctx.beginPath();
                            ctx.moveTo(touch.clientX - rect.left, touch.clientY - rect.top);
                            validateModalInputs();
                        }
                        e.preventDefault();
                    });

                    canvas.addEventListener('touchmove', e => {
                        if (!isDrawing || e.touches.length === 0) return;
                        const touch = e.touches[0];
                        const rect = canvas.getBoundingClientRect();
                        ctx.lineTo(touch.clientX - rect.left, touch.clientY - rect.top);
                        ctx.stroke();
                        e.preventDefault();
                    });

                    canvas.addEventListener('touchend', () => isDrawing = false);
                    canvas.addEventListener('touchcancel', () => isDrawing = false);
                }

                document.getElementById('clear-canvas').addEventListener('click', () => {
                    ctx.clearRect(0, 0, canvas.width, canvas.height);
                    hasDrawn = false;
                    validateModalInputs();
                });

                document.getElementById('color-black').addEventListener('click', function() {
                    inkColor = '#000000';
                    ctx.strokeStyle = inkColor;
                    this.classList.add('active');
                    document.getElementById('color-blue').classList.remove('active');
                });

                document.getElementById('color-blue').addEventListener('click', function() {
                    inkColor = '#0000FF';
                    ctx.strokeStyle = inkColor;
                    this.classList.add('active');
                    document.getElementById('color-black').classList.remove('active');
                });

                document.getElementById('draw-tab').addEventListener('shown.bs.tab', () => {
                    signatureMode = 'draw';
                    validateModalInputs();
                });
                document.getElementById('type-tab').addEventListener('shown.bs.tab', () => {
                    signatureMode = 'type';
                    validateModalInputs();
                });
                document.getElementById('upload-tab').addEventListener('shown.bs.tab', () => {
                    signatureMode = 'upload';
                    validateModalInputs();
                });

                document.getElementById('typed-name').addEventListener('input', function() {
                    document.querySelectorAll('.font-select-card .preview-text').forEach(el => {
                        el.textContent = this.value || 'Name';
                    });
                    validateModalInputs();
                });

                document.querySelectorAll('.font-select-card').forEach(card => {
                    card.addEventListener('click', function() {
                        document.querySelectorAll('.font-select-card').forEach(c => c.classList.remove('active'));
                        this.classList.add('active');
                        selectedFont = this.dataset.font;
                    });
                });

                document.getElementById('upload-signature-file').addEventListener('change', e => {
                    const file = e.target.files[0];
                    if (!file) return;
                    
                    const reader = new FileReader();
                    reader.onload = function(evt) {
                        uploadedBase64 = evt.target.result;
                        document.getElementById('upload-preview').src = uploadedBase64;
                        document.getElementById('upload-preview-container').classList.remove('d-none');
                        validateModalInputs();
                    };
                    reader.readAsDataURL(file);
                });

                document.getElementById('consent-check').addEventListener('change', validateModalInputs);

                function validateModalInputs() {
                    let valid = false;
                    if (signatureMode === 'draw') valid = hasDrawn;
                    else if (signatureMode === 'type') valid = document.getElementById('typed-name').value.trim().length > 0;
                    else if (signatureMode === 'upload') valid = !!uploadedBase64;

                    const btn = document.getElementById('adopt-signature-btn');
                    if (valid) {
                        btn.classList.remove('disabled');
                        btn.removeAttribute('disabled');
                    } else {
                        btn.classList.add('disabled');
                        btn.setAttribute('disabled', 'disabled');
                    }
                }

                function getTypedImage() {
                    const text = document.getElementById('typed-name').value || '';
                    const temp = document.createElement('canvas');
                    temp.width = 300;
                    temp.height = 100;
                    const tempCtx = temp.getContext('2d');
                    tempCtx.fillStyle = inkColor;
                    tempCtx.font = selectedFont === 'Caveat' ? "bold italic 32px 'Caveat', cursive" : "22px 'Pacifico', cursive";
                    tempCtx.textAlign = 'center';
                    tempCtx.textBaseline = 'middle';
                    tempCtx.fillText(text, temp.width / 2, temp.height / 2);
                    return temp.toDataURL('image/png');
                }

                // Adopt Signature Confirm
                document.getElementById('adopt-signature-btn').addEventListener('click', function() {
                    const checked = document.getElementById('consent-check').checked;
                    if (!checked) {
                        const consentLabel = document.querySelector('.form-check-label');
                        consentLabel.style.color = '#dc3545';
                        consentLabel.classList.add('fw-bold');
                        alert('Please check the agreement checkbox to adopt and sign your signature.');
                        return;
                    }
                    if (!currentTargetField) return;
                    const { item, box } = currentTargetField;
                    
                    let dataUrl = '';
                    if (signatureMode === 'draw') dataUrl = canvas.toDataURL('image/png');
                    else if (signatureMode === 'type') dataUrl = getTypedImage();
                    else if (signatureMode === 'upload') dataUrl = uploadedBase64;
                    
                    fieldsState[item.id] = { value: '', signature: dataUrl };
                    
                    box.classList.add('filled');
                    box.innerHTML = `<img src="${dataUrl}"/>`;
                    
                    bootstrap.Modal.getInstance(document.getElementById('signatureModal')).hide();
                    validateCompletion();
                });

                function validateCompletion() {
                    const requiredItems = templateItems.filter(isFieldInteractive);
                    const allFilled = requiredItems.every(item => !!fieldsState[item.id]);
                    
                    const btn = document.getElementById('submit-signature');
                    const progress = document.getElementById('signing-progress-text');
                    
                    if (allFilled) {
                        btn.classList.remove('disabled');
                        btn.removeAttribute('disabled');
                        progress.textContent = "All required fields completed. You can now submit your signature.";
                        progress.className = "small mb-3 text-success fw-bold";
                    } else {
                        btn.classList.add('disabled');
                        btn.setAttribute('disabled', 'disabled');
                        progress.textContent = "Please fill all the blue fields highlighted on the document.";
                        progress.className = "small mb-3 text-warning";
                    }
                }

                // Final Submission
                document.getElementById('submit-signature').addEventListener('click', function() {
                    this.disabled = true;
                    this.textContent = "Submitting...";
                    
                    const payload = [];
                    const requiredItems = templateItems.filter(isFieldInteractive);
                    
                    requiredItems.forEach(item => {
                        const state = fieldsState[item.id];
                        payload.push({
                            item_id: item.id,
                            value: state.value || '',
                            signature: state.signature || ''
                        });
                    });
                    
                    fetch('/wm_signature/sign/submit', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json'
                        },
                        body: JSON.stringify({
                            params: {
                                token: token,
                                filled_fields: payload
                            }
                        })
                    })
                    .then(r => r.json())
                    .then(data => {
                        if (data.result && data.result.success) {
                            window.location.href = data.result.redirect_url;
                        } else {
                            alert("Error: " + (data.result ? data.result.error : (data.error || "Failed to submit signature")));
                            this.disabled = false;
                            this.innerHTML = '<i class="fa fa-check me-1"></i> Sign Document';
                        }
                    })
                    .catch(err => {
                        console.error(err);
                        alert("Network error.");
                        this.disabled = false;
                        this.innerHTML = '<i class="fa fa-check me-1"></i> Sign Document';
                    });
                });
})();
