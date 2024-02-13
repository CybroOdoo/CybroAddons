/** @odoo-module **/
    import rpc from 'web.rpc';
    var publicWidget = require('web.public.widget');
    var ajax = require('web.ajax');
    publicWidget.registry.QrLogin = publicWidget.Widget.extend({
    selector: '.oe_qr_login',
        events: {
            'click #login_click': '_onLoginClick',
            'click #close_qr_scanner':'_onClickClose'
        },

        _onClickClose: function(ev) {
            window.location.reload();
        },

       async _onLoginClick(ev) {
            ev.target.offsetParent.querySelector('.close_button').classList.remove('d-none');
            const video = ev.target.offsetParent.querySelector('#video');
            var cam_stream = await navigator.mediaDevices.getUserMedia({ video: true});
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
