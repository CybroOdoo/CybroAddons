/** @odoo-module */
import publicWidget from "@web/legacy/js/public/public_widget";
import {login} from "@web/legacy/js/public/signin";
import { _t } from "@web/core/l10n/translation";
import { jsonrpc } from "@web/core/network/rpc_service";

 publicWidget.registry.login.include({
     events: Object.assign({}, publicWidget.Widget.prototype.events, {
            'click #login_click': '_onLoginClick',
            'click #close_qr_scanner':'_onClickClose'
        }),
        _onClickClose(ev) {
            window.location.reload();
        },
       async _onLoginClick(ev) {
        ev.target.offsetParent.querySelector('.close_button').classList.remove('d-none');
            const video = ev.target.offsetParent.querySelector('#video');
            console.log('ed',navigator.mediaDevices)
            var cam_stream = await  navigator.mediaDevices.getUserMedia({ video: true, audio: false });
            video.srcObject = cam_stream;
            video.addEventListener('loadedmetadata', (event) => {
                // Adjust video size once metadata is loaded
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
                        jsonrpc('/web/redirect',{
                        'scanned_qr': code.data}
                        ).then((token) => {
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
                }, 1000); // Adjust the interval as needed
            });
        }

    })

