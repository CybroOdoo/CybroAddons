// Signature template designer logic. Page data is read from #wm-editor-config.
window.bootstrap = window.bootstrap || {Modal: window.Modal, Tab: window.Tab};
(function () {
                const config = document.getElementById('wm-editor-config').dataset;
                const templateId = parseInt(config.templateId, 10);
                const orderId = config.orderId;
                const inspectionId = config.inspectionId;
                const rolesMap = {};
                document.querySelectorAll('#wm-editor-config .wm-editor-role').forEach(el => {
                    rolesMap[el.dataset.id] = {
                        name: el.dataset.name, color: el.dataset.color, borderColor: el.dataset.borderColor,
                    };
                });

                let fieldsList = [];
                let newFieldSeq = 0; // keeps ids unique when fields are dropped within the same millisecond
                let activeField = null;

                // Load existing fields
                const existingFields = JSON.parse(config.existingItems);

                // Setup Draggable Items from sidebar
                document.querySelectorAll('.draggable-field-item').forEach(item => {
                    item.addEventListener('dragstart', function(e) {
                        e.dataTransfer.setData('field-type', this.dataset.type);
                    });
                });

                // ---- IFRAME PDF LOADING ----
                let pdfUrl = `/wm_signature/template/pdf/${templateId}`;
                if (inspectionId) {
                    pdfUrl += `?inspection_id=${encodeURIComponent(inspectionId)}`;
                } else if (orderId) {
                    pdfUrl += `?order_id=${encodeURIComponent(orderId)}`;
                }
                const pdfCanvas = document.getElementById('pdf-canvas');
                const pdfOverlay = document.getElementById('pdf-overlay');

                async function renderPdfPage() {
                    const lib = window.pdfjsLib || window['pdfjs-dist/build/pdf'] || (typeof globalThis !== 'undefined' && globalThis['pdfjs-dist/build/pdf']);
                    if (!pdfCanvas || !pdfOverlay || !lib) {
                        console.error('PDF library or canvas not available in template editor:', { pdfCanvas, pdfOverlay, lib });
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
                        const context = pdfCanvas.getContext('2d');

                        pdfCanvas.width = viewport.width;
                        pdfCanvas.height = viewport.height;
                        pdfCanvas.style.width = `${viewport.width}px`;
                        pdfCanvas.style.height = `${viewport.height}px`;
                        pdfOverlay.style.width = `${viewport.width}px`;
                        pdfOverlay.style.height = `${viewport.height}px`;
                        pdfOverlay.innerHTML = '';

                        await page.render({
                            canvasContext: context,
                            viewport: viewport,
                        }).promise;

                        pdfOverlay.style.pointerEvents = 'all';

                        if (existingFields && existingFields.length) {
                            existingFields.forEach(f => {
                                createFieldBox(f, pdfOverlay);
                            });
                        }
                        setupDropZone(pdfOverlay, 1);
                    } catch (error) {
                        console.error('Failed to render PDF in template editor:', error);
                        pdfOverlay.style.pointerEvents = 'all';
                        pdfOverlay.innerHTML = `
                            <div style="position:absolute;inset:0;display:flex;align-items:center;justify-content:center;color:#fff;background:#333;padding:24px;text-align:center;">
                                <div>
                                    <div style="font-size:18px;font-weight:600;margin-bottom:8px;">Unable to load document preview</div>
                                    <a href="${pdfUrl}" target="_blank" style="color:#8ec5ff;text-decoration:underline;">Open PDF in a new tab</a>
                                </div>
                            </div>
                        `;
                    }
                }
                renderPdfPage();

                function setupDropZone(overlay, pageNum) {
                    overlay.addEventListener('dragover', e => e.preventDefault());
                    overlay.addEventListener('drop', e => {
                        e.preventDefault();
                        const fieldType = e.dataTransfer.getData('field-type');
                        if (!fieldType) return;

                        const rect = overlay.getBoundingClientRect();
                        const x = ((e.clientX - rect.left) / rect.width) * 100;
                        const y = ((e.clientY - rect.top) / rect.height) * 100;

                        const defaultRole = document.getElementById('default-signer-role').value;

                        const newField = {
                            id: 'new_' + Date.now() + '_' + (++newFieldSeq),
                            page: pageNum,
                            x: x,
                            y: y,
                            width: 20,
                            height: 4.5,
                            type: fieldType,
                            role_id: defaultRole
                        };

                        createFieldBox(newField, overlay);
                    });

                }

                function createFieldBox(field, overlay) {
                    const box = document.createElement('div');
                    box.className = 'field-box';
                    box.dataset.id = field.id;
                    box.style.left = field.x + '%';
                    box.style.top = field.y + '%';
                    box.style.width = field.width + '%';
                    box.style.height = field.height + '%';
                    
                    const roleInfo = rolesMap[field.role_id] || { name: 'Unknown', color: '#555', borderColor: '#777' };
                    box.style.backgroundColor = roleInfo.color;
                    box.style.borderColor = roleInfo.borderColor;
                    box.style.color = roleInfo.borderColor;

                    const iconClass = field.type === 'signature' ? 'fa-pencil text-primary' : 'fa-tag';
                    const labelText = field.type === 'signature' ? 'Signature' : field.type;

                    const content = `
                        <div class="d-flex flex-column align-items-start w-100">
                            <span class="field-label text-capitalize small fw-bold">
                                <i class="fa ${iconClass} me-1"></i>${labelText}
                            </span>
                            <span class="role-badge" style="background-color: ${roleInfo.borderColor}">${roleInfo.name}</span>
                        </div>
                        <span class="delete-btn">&#215;</span>
                    `;
                    box.innerHTML = content;
                    overlay.appendChild(box);

                    // Add to local state
                    fieldsList.push(field);

                    // Make Draggable inside overlay
                    let startX = 0, startY = 0;
                    box.addEventListener('mousedown', function(e) {
                        if (e.target.className === 'delete-btn') return;
                        
                        e.preventDefault();
                        selectField(field, box);
                        
                        startX = e.clientX;
                        startY = e.clientY;
                        
                        const onMouseMove = ev => {
                            const dx = ev.clientX - startX;
                            const dy = ev.clientY - startY;
                            startX = ev.clientX;
                            startY = ev.clientY;
                            
                            const rect = overlay.getBoundingClientRect();
                            const xChange = (dx / rect.width) * 100;
                            const yChange = (dy / rect.height) * 100;
                            
                            field.x = Math.max(0, Math.min(100 - field.width, field.x + xChange));
                            field.y = Math.max(0, Math.min(100 - field.height, field.y + yChange));
                            
                            box.style.left = field.x + '%';
                            box.style.top = field.y + '%';
                        };
                        
                        const onMouseUp = () => {
                            document.removeEventListener('mousemove', onMouseMove);
                            document.removeEventListener('mouseup', onMouseUp);
                        };
                        
                        document.addEventListener('mousemove', onMouseMove);
                        document.addEventListener('mouseup', onMouseUp);
                    });

                    // Delete Handler
                    box.querySelector('.delete-btn').addEventListener('click', function(e) {
                        e.stopPropagation();
                        box.remove();
                        fieldsList = fieldsList.filter(f => f.id !== field.id);
                        if (activeField && activeField.id === field.id) {
                            deselectField();
                        }
                    });
                }

                function selectField(field, box) {
                    activeField = field;
                    document.querySelectorAll('.field-box').forEach(b => b.classList.remove('active'));
                    box.classList.add('active');
                    
                    document.getElementById('no-field-selected').classList.add('d-none');
                    const controls = document.getElementById('field-selected-controls');
                    controls.classList.remove('d-none');
                    
                    const roleSelect = document.getElementById('field-role-select');
                    roleSelect.value = field.role_id;
                    
                    roleSelect.onchange = function() {
                        field.role_id = this.value;
                        const newRoleInfo = rolesMap[field.role_id] || { name: 'Unknown', color: '#555', borderColor: '#777' };
                        box.style.backgroundColor = newRoleInfo.color;
                        box.style.borderColor = newRoleInfo.borderColor;
                        box.style.color = newRoleInfo.borderColor;
                        box.querySelector('.role-badge').textContent = newRoleInfo.name;
                        box.querySelector('.role-badge').style.backgroundColor = newRoleInfo.borderColor;
                    };
                }

                function deselectField() {
                    activeField = null;
                    document.getElementById('no-field-selected').classList.remove('d-none');
                    document.getElementById('field-selected-controls').classList.add('d-none');
                }

                document.getElementById('delete-selected-field').addEventListener('click', function() {
                    if (!activeField) return;
                    const box = document.querySelector(`.field-box[data-id="${activeField.id}"]`);
                    if (box) box.remove();
                    fieldsList = fieldsList.filter(f => f.id !== activeField.id);
                    deselectField();
                });

                // Save Handler
                document.getElementById('save-template-fields').addEventListener('click', function() {
                    this.disabled = true;
                    this.textContent = "Saving...";
                    
                    fetch('/wm_signature/template/save_fields', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json'
                        },
                        body: JSON.stringify({
                            params: {
                                template_id: templateId,
                                fields_data: fieldsList
                            }
                        })
                    })
                    .then(r => r.json())
                    .then(data => {
                        this.disabled = false;
                        this.innerHTML = '<i class="fa fa-save me-1"></i> Save Fields';
                        if (data.result && data.result.success) {
                            alert("Template fields saved successfully!");
                        } else {
                            alert("Error: " + (data.error || "Failed to save fields"));
                        }
                    })
                    .catch(err => {
                        this.disabled = false;
                        this.innerHTML = '<i class="fa fa-save me-1"></i> Save Fields';
                        console.error(err);
                        alert("Network error. Please try again.");
                    });
                });

                // Sign Now Handler
                const signNowBtn = document.getElementById('sign-now-button');
                if (signNowBtn) {
                    signNowBtn.addEventListener('click', function() {
                        this.disabled = true;
                        this.textContent = "Saving & Preparing Document...";
                        
                        // First save template fields
                        fetch('/wm_signature/template/save_fields', {
                            method: 'POST',
                            headers: {
                                'Content-Type': 'application/json'
                            },
                            body: JSON.stringify({
                                params: {
                                    template_id: templateId,
                                    fields_data: fieldsList
                                }
                            })
                        })
                        .then(r => r.json())
                        .then(data => {
                            if (data.result && data.result.success) {
                                // Now invoke sign_now controller endpoint
                                const urlParams = new URLSearchParams(window.location.search);
                                return fetch('/wm_signature/template/sign_now', {
                                    method: 'POST',
                                    headers: {
                                        'Content-Type': 'application/json'
                                    },
                                    body: JSON.stringify({
                                        params: {
                                            template_id: templateId,
                                            order_id: orderId,
                                            inspection_id: inspectionId
                                        }
                                    })
                                });
                            } else {
                                throw new Error((data.result && data.result.error) || data.error || "Failed to save fields");
                            }
                        })
                        .then(r => r.json())
                        .then(data => {
                            if (data.result && data.result.success && data.result.redirect_url) {
                                window.location.href = data.result.redirect_url;
                            } else {
                                throw new Error((data.result && data.result.error) || data.error || "Failed to initialize signature request");
                            }
                        })
                        .catch(err => {
                            this.disabled = false;
                            this.innerHTML = '<i class="fa fa-pencil me-1"></i> Sign Now';
                            console.error(err);
                            alert("Error: " + err.message);
                        });
                    });
                }

                // Customize Back button for Iframe / Backend Mode
                const backBtn = document.getElementById('back-to-odoo-btn');
                if (backBtn && window.self !== window.top) {
                    backBtn.textContent = 'Cancel';
                    backBtn.className = 'btn btn-outline-danger btn-sm me-3';
                    backBtn.href = '#';
                    backBtn.addEventListener('click', function(e) {
                        e.preventDefault();
                        window.parent.postMessage({ type: 'discard' }, '*');
                    });
                }

                // Send Request Handler
                const sendBtn = document.getElementById('send-request-button');
                if (sendBtn) {
                    sendBtn.addEventListener('click', function() {
                        sendBtn.disabled = true;
                        sendBtn.textContent = "Saving Fields...";
                        
                        // Save fields first
                        fetch('/wm_signature/template/save_fields', {
                            method: 'POST',
                            headers: {
                                'Content-Type': 'application/json'
                            },
                            body: JSON.stringify({
                                params: {
                                    template_id: templateId,
                                    fields_data: fieldsList
                                }
                            })
                        })
                        .then(r => r.json())
                        .then(data => {
                            sendBtn.disabled = false;
                            sendBtn.innerHTML = '<i class="fa fa-paper-plane me-1"></i> Send';
                            
                            if (data.result && data.result.success) {
                                // Build modal inputs dynamically
                                const container = document.getElementById('signer-inputs-container');
                                container.innerHTML = '';
                                
                                for (const roleId in rolesMap) {
                                    const roleName = rolesMap[roleId].name;
                                    container.innerHTML += `
                                        <div class="mb-3 border-bottom pb-3">
                                            <h6 class="fw-bold text-primary">${roleName}</h6>
                                            <div class="row g-2">
                                                <div class="col-6">
                                                    <label class="form-label small text-muted mb-1">Name</label>
                                                    <input type="text" class="form-control form-control-sm signer-name-input" data-role-id="${roleId}" required="required" placeholder="Name"/>
                                                </div>
                                                <div class="col-6">
                                                    <label class="form-label small text-muted mb-1">Email</label>
                                                    <input type="email" class="form-control form-control-sm signer-email-input" data-role-id="${roleId}" required="required" placeholder="Email"/>
                                                </div>
                                            </div>
                                        </div>
                                    `;
                                }
                                
                                const sendModal = new bootstrap.Modal(document.getElementById('sendRequestModal'));
                                sendModal.show();
                            } else {
                                alert("Error: " + (data.result?.error || data.error || "Failed to save fields"));
                            }
                        })
                        .catch(err => {
                            sendBtn.disabled = false;
                            sendBtn.innerHTML = '<i class="fa fa-paper-plane me-1"></i> Send';
                            console.error(err);
                            alert("Network error.");
                        });
                    });
                }

                // Confirm Send Request Handler
                const confirmSendBtn = document.getElementById('confirm-send-request-btn');
                if (confirmSendBtn) {
                    confirmSendBtn.addEventListener('click', function() {
                        const signers = [];
                        let isValid = true;
                        
                        document.querySelectorAll('.signer-name-input').forEach(nameInput => {
                            const roleId = nameInput.dataset.roleId;
                            const emailInput = document.querySelector(`.signer-email-input[data-role-id="${roleId}"]`);
                            
                            const name = nameInput.value.trim();
                            const email = emailInput ? emailInput.value.trim() : '';
                            
                            if (!name || !email) {
                                isValid = false;
                                nameInput.classList.add('is-invalid');
                                if (emailInput) emailInput.classList.add('is-invalid');
                            } else {
                                nameInput.classList.remove('is-invalid');
                                if (emailInput) emailInput.classList.remove('is-invalid');
                                signers.push({ role_id: roleId, name, email });
                            }
                        });
                        
                        if (!isValid) {
                            alert("Please fill name and email for all signers.");
                            return;
                        }
                        
                        confirmSendBtn.disabled = true;
                        confirmSendBtn.textContent = "Sending...";
                        
                        fetch('/wm_signature/template/send_request', {
                            method: 'POST',
                            headers: {
                                'Content-Type': 'application/json'
                            },
                            body: JSON.stringify({
                                params: {
                                    template_id: templateId,
                                    signers: signers
                                }
                            })
                        })
                        .then(r => r.json())
                        .then(data => {
                            confirmSendBtn.disabled = false;
                            confirmSendBtn.textContent = "Send Request";
                            
                            if (data.result && data.result.success) {
                                const modalEl = document.getElementById('sendRequestModal');
                                const modalInst = bootstrap.Modal.getInstance(modalEl);
                                if (modalInst) modalInst.hide();
                                
                                if (window.self !== window.top) {
                                    window.parent.postMessage({ type: 'send_complete' }, '*');
                                } else {
                                    alert("Signature request successfully sent!");
                                    window.location.href = `/web#model=wm.signature.template&id=${templateId}&view_type=form`;
                                }
                            } else {
                                alert("Error: " + (data.result?.error || data.error || "Failed to send request"));
                            }
                        })
                        .catch(err => {
                            confirmSendBtn.disabled = false;
                            confirmSendBtn.textContent = "Send Request";
                            console.error(err);
                            alert("Network error.");
                        });
                    });
                }
})();
