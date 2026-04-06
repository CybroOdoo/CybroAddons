/** @odoo-module */

import { Login } from "@web/public/login";
import { rpc } from "@web/core/network/rpc";
import { patch } from "@web/core/utils/patch";
import { _t } from "@web/core/l10n/translation";

//Patch the Login class to add QR code login functionality
patch(Login.prototype, {
    setup() {
        super.setup();
        document.addEventListener('click', (event) => {
            if (event.target.closest('#login_click')) {
                event.preventDefault();
                event.stopPropagation();
                this._onLoginClick(event);
            }
            if (event.target.closest('#close_qr_scanner')) {
                event.preventDefault();
                event.stopPropagation();
                this._onClickClose(event);
            }
        });
    },

   _onClickClose(ev) {
        const video = document.querySelector('#video');
        if (video && video.srcObject) {
            video.srcObject.getTracks().forEach(track => track.stop());
        }
        document.querySelector('.close_button').classList.add('d-none');
        document.querySelector('.video-container').classList.add('d-none');
    },

   async _onLoginClick(ev) {
        const closeBtn = document.querySelector('.close_button');
        const videoContainer = document.querySelector('.video-container');
        const video = ev.target.offsetParent.querySelector('#video');
        if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
            alert("Camera access is blocked. Please open this page using a secure (HTTPS) connection.");
            return;
        }
        else{
            closeBtn.classList.remove('d-none');
            videoContainer.classList.remove('d-none');
            ev.target.offsetParent.querySelector('.close_button').classList.remove('d-none');
            var cam_stream = await  navigator.mediaDevices.getUserMedia({ video: true, audio: false });
        }
        video.srcObject = cam_stream;
        video.addEventListener('loadedmetadata', (event) => {
            video.width = video.videoWidth;
            video.height = video.videoHeight;
        });
        video.addEventListener('canplay', () => {
            const canvas = document.createElement('canvas');
            const context = canvas.getContext('2d');
            canvas.width = video.width;
            canvas.height = video.height;
            setInterval(() => {
                context.drawImage(video, 0, 0, canvas.width, canvas.height);
                const imageData = context.getImageData(0, 0, canvas.width, canvas.height);
                const code = jsQR(imageData.data, imageData.width, imageData.height);
                if (code) {
                    rpc('/web/redirect',{
                        scanned_qr: code.data
                    }).then((token) => {
                        if(token){
                            cam_stream.getTracks().forEach(function(track) {
                                track.stop();
                                window.location.href = '/';
                            });
                        }
                        else{
                            alert('Scanned QR does not exist. Please try again.');
                            window.location.reload();
                        }
                    });
                }
            }, 1000);
        });
    }
});