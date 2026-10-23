/** @odoo-module */

import { Login } from "@web/public/login";
import { rpc } from "@web/core/network/rpc";
import { patch } from "@web/core/utils/patch";
import { _t } from "@web/core/l10n/translation";

// Patch the public Login interaction to add QR code login functionality
patch(Login.prototype, {
    setup() {
        super.setup();
        this.scanInterval = null;
        this.camStream = null;
        this.dynamicContent = {
            ...this.dynamicContent,
            "#login_click": { "t-on-click.prevent.stop": this.onQrLoginClick },
            "#close_qr_scanner, .scanner-overlay": {
                "t-on-click.prevent.stop": this.onQrClose,
            },
        };
    },

    destroy() {
        super.destroy();
        this.onQrClose();
    },

    _showError(message) {
        let errEl = this.el.querySelector('.oe_qr_login_error');
        if (!errEl) {
            errEl = document.createElement('div');
            errEl.className = 'oe_qr_login_error alert alert-danger mt-2 py-1 px-2';
            errEl.setAttribute('role', 'alert');
            (this.el.querySelector('.oe_qr_login') || this.el).appendChild(errEl);
        }
        errEl.textContent = message;
        errEl.classList.remove('d-none');
    },

    _clearError() {
        const errEl = this.el.querySelector('.oe_qr_login_error');
        if (errEl) {
            errEl.classList.add('d-none');
            errEl.textContent = '';
        }
    },

    onQrClose() {
        this._clearError();
        if (this.scanInterval) {
            clearInterval(this.scanInterval);
            this.scanInterval = null;
        }
        if (this.camStream) {
            this.camStream.getTracks().forEach(track => track.stop());
            this.camStream = null;
        }
        const video = this.el.querySelector('#video');
        if (video && video.srcObject) {
            video.srcObject.getTracks().forEach(track => track.stop());
            video.srcObject = null;
        }
        const overlay = this.el.querySelector('.scanner-overlay');
        if (overlay) overlay.classList.add('d-none');
        const closeBtn = this.el.querySelector('.close_button');
        if (closeBtn) closeBtn.classList.add('d-none');
        const videoContainer = this.el.querySelector('.video-container');
        if (videoContainer) videoContainer.classList.add('d-none');
    },

    async onQrLoginClick() {
        this._clearError();
        const overlay = this.el.querySelector('.scanner-overlay');
        const closeBtn = this.el.querySelector('.close_button');
        const videoContainer = this.el.querySelector('.video-container');
        const video = this.el.querySelector('#video');

        if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
            this._showError(_t("Camera access is blocked. Please open this page using a secure (HTTPS) connection."));
            return;
        }

        try {
            this.camStream = await navigator.mediaDevices.getUserMedia({
                video: { facingMode: "environment" },
                audio: false,
            });
        } catch (err) {
            this._showError(_t("Unable to access camera: %(error)s", { error: err.message }));
            return;
        }

        if (overlay) overlay.classList.remove('d-none');
        if (closeBtn) closeBtn.classList.remove('d-none');
        if (videoContainer) videoContainer.classList.remove('d-none');

        if (video) {
            video.srcObject = this.camStream;
            video.onloadedmetadata = () => {
                video.play();
                video.width = video.videoWidth || 640;
                video.height = video.videoHeight || 480;
            };

            const canvas = document.createElement('canvas');
            const context = canvas.getContext('2d');

            if (this.scanInterval) {
                clearInterval(this.scanInterval);
                this.scanInterval = null;
            }

            let isProcessing = false;
            this.scanInterval = setInterval(() => {
                if (isProcessing || !video.videoWidth || !video.videoHeight) {
                    return;
                }
                canvas.width = video.videoWidth;
                canvas.height = video.videoHeight;
                context.drawImage(video, 0, 0, canvas.width, canvas.height);
                const imageData = context.getImageData(0, 0, canvas.width, canvas.height);
                if (typeof jsQR === 'function') {
                    const code = jsQR(imageData.data, imageData.width, imageData.height);
                    if (code && code.data) {
                        isProcessing = true;
                        rpc('/login_using_qr/authenticate', {
                            scanned_qr: code.data,
                        }).then((success) => {
                            if (success) {
                                if (this.scanInterval) {
                                    clearInterval(this.scanInterval);
                                    this.scanInterval = null;
                                }
                                if (this.camStream) {
                                    this.camStream.getTracks().forEach(track => track.stop());
                                    this.camStream = null;
                                }
                                const urlParams = new URLSearchParams(window.location.search);
                                const redirectUrl = urlParams.get('redirect') || '/odoo';
                                window.location.href = redirectUrl;
                            } else {
                                this._showError(_t('Scanned QR code is invalid or unauthorized. Please try again.'));
                                setTimeout(() => {
                                    isProcessing = false;
                                }, 1500);
                            }
                        }).catch((error) => {
                            console.error("QR Code redirect error:", error);
                            const errMsg = (error.data && error.data.message) || error.message || _t("Server error");
                            this._showError(_t("Error during QR login: %(error)s", { error: errMsg }));
                            setTimeout(() => {
                                isProcessing = false;
                            }, 1500);
                        });
                    }
                }
            }, 500);
        }
    }
});