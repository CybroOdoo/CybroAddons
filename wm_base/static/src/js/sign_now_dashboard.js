/** @odoo-module */
import { registry } from "@web/core/registry";
import { Component, useState, useRef, onWillDestroy } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";
import { rpc } from "@web/core/network/rpc";
import { _t } from "@web/core/l10n/translation";

export class WmSignatureSignNow extends Component {
    setup() {
        this.notification = useService('notification');
        this.fileInput = useRef('fileInput');

        this.state = useState({
            mode: 'upload', // 'upload' or 'edit'
            templateId: null,
            isDragging: false,
            isLoading: false,
            loadingMessage: '',
        });

        this.onMessage = this.onMessage.bind(this);
        window.addEventListener('message', this.onMessage);
        
        onWillDestroy(() => {
            window.removeEventListener('message', this.onMessage);
        });
    }

    get editorUrl() {
        return `/wm_signature/template/edit/${this.state.templateId}?backend=1`;
    }

    onMessage(ev) {
        if (ev.data && ev.data.type === 'signature_complete') {
            this.notification.add(_t("Document successfully signed!"), {
                type: 'success',
            });
            this.state.mode = 'upload';
            this.state.templateId = null;
        } else if (ev.data && ev.data.type === 'send_complete') {
            this.notification.add(_t("Signature request successfully sent!"), {
                type: 'success',
            });
            this.state.mode = 'upload';
            this.state.templateId = null;
        } else if (ev.data && ev.data.type === 'discard') {
            this.state.mode = 'upload';
            this.state.templateId = null;
        }
    }

    triggerUpload() {
        if (this.fileInput.el) {
            this.fileInput.el.click();
        }
    }

    async onFileChange(ev) {
        const file = ev.target.files[0];
        if (!file) return;
        
        if (file.type !== 'application/pdf') {
            this.notification.add(_t("Only PDF documents are allowed."), {
                type: 'danger',
            });
            return;
        }
 
        this.state.isLoading = true;
        this.state.loadingMessage = _t("Uploading and preparing PDF document...");
 
        try {
            const base64Data = await this._readAsBase64(file);
            const result = await rpc('/wm_signature/template/create_from_pdf', {
                name: file.name,
                document_base64: base64Data,
                filename: file.name,
            });
 
            if (result.success && result.template_id) {
                this.state.templateId = result.template_id;
                this.state.mode = 'edit';
            } else {
                this.notification.add(result.error || _t("Failed to upload document."), {
                    type: 'danger',
                });
            }
        } catch (err) {
            console.error("Upload error:", err);
            this.notification.add(_t("Network error during upload."), {
                type: 'danger',
            });
        } finally {
            this.state.isLoading = false;
            // Clear input
            if (this.fileInput.el) this.fileInput.el.value = '';
        }
    }

    async createSample() {
        this.state.isLoading = true;
        this.state.loadingMessage = _t("Generating sample contract PDF...");
 
        try {
            const result = await rpc('/wm_signature/template/create_sample', {});
            if (result.success && result.template_id) {
                this.state.templateId = result.template_id;
                this.state.mode = 'edit';
            } else {
                this.notification.add(result.error || _t("Failed to generate sample contract."), {
                    type: 'danger',
                });
            }
        } catch (err) {
            console.error("Sample creation error:", err);
            this.notification.add(_t("Network error during sample generation."), {
                type: 'danger',
            });
        } finally {
            this.state.isLoading = false;
        }
    }

    closeEditor() {
        this.state.mode = 'upload';
        this.state.templateId = null;
    }

    // Drag and drop handlers
    onDragOver(ev) {
        this.state.isDragging = true;
    }

    onDragEnter(ev) {
        this.state.isDragging = true;
    }

    onDragLeave(ev) {
        this.state.isDragging = false;
    }

    async onDrop(ev) {
        this.state.isDragging = false;
        const file = ev.dataTransfer.files[0];
        if (!file) return;
 
        if (file.type !== 'application/pdf') {
            this.notification.add(_t("Only PDF documents are allowed."), {
                type: 'danger',
            });
            return;
        }
 
        this.state.isLoading = true;
        this.state.loadingMessage = _t("Processing dropped PDF document...");
 
        try {
            const base64Data = await this._readAsBase64(file);
            const result = await rpc('/wm_signature/template/create_from_pdf', {
                name: file.name,
                document_base64: base64Data,
                filename: file.name,
            });
 
            if (result.success && result.template_id) {
                this.state.templateId = result.template_id;
                this.state.mode = 'edit';
            } else {
                this.notification.add(result.error || _t("Failed to process document."), {
                    type: 'danger',
                });
            }
        } catch (err) {
            console.error("Drop process error:", err);
            this.notification.add(_t("Network error during drop handling."), {
                type: 'danger',
            });
        } finally {
            this.state.isLoading = false;
        }
    }

    _readAsBase64(file) {
        return new Promise((resolve, reject) => {
            const reader = new FileReader();
            reader.onload = () => resolve(reader.result);
            reader.onerror = error => reject(error);
            reader.readAsDataURL(file);
        });
    }
}

WmSignatureSignNow.template = "wm_base.SignNowDashboard";
registry.category("actions").add("wm_base.sign_now", WmSignatureSignNow);
