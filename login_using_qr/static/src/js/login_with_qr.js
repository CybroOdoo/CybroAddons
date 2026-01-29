odoo.define('login_using_qr.qr_login', function (require) {
    'use strict';
    var publicWidget = require('web.public.widget');
    var ajax = require('web.ajax');
//    var Dialog = require('web.Dialog');
    var rpc = require('web.rpc')
    var core = require('web.core');
//    var session = require('web.session');

    var _t = core._t;
    publicWidget.registry.QrLogin = publicWidget.Widget.extend({
    selector: '.oe_qr_login',
        events: {
            'click #login_click': '_onLoginClick',
            'click #close_qr_scanner':'_onClickClose'
        },

        _onClickClose: function(ev) {
            window.location.reload();
        },

        _onLoginClick: function(ev) {
             $(ev.target.offsetParent.querySelector('.qr_video')).removeClass('d-none');
             $(ev.target.offsetParent.querySelector('.close_button')).removeClass('d-none');
            const video = ev.target.offsetParent.querySelector('#video');
            var cam_stream
            navigator.mediaDevices.getUserMedia({ video: true })
                .then((stream) => {
                    cam_stream = stream
                    video.srcObject = stream;
                })
                .catch((error) => {
                });
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
                        ajax.jsonRpc('/web/redirect', 'call', {'scanned_qr': code.data}
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
});
