odoo.define('odoo_screen_recording.video', function (require) {
    "use strict";
    var SystrayMenu = require('web.SystrayMenu');
    var Widget = require('web.Widget');
    var rpc = require("web.rpc");
    var VideoButton = Widget.extend({
        template: 'ScreenCaptureSystray',
        events: {
            'click #capture_screen': '_onClick',
        },
        _onClick: function () {
            try {
                // Get display media stream
                navigator.mediaDevices.getDisplayMedia({ video: true })
                    .then(stream => {
                        // Change button color to indicate recording
                        let icon = document.querySelector(".record");
                        icon.style.color = '#28a745';

                        // Set up media recorder
                        const mime = MediaRecorder.isTypeSupported("video/webm; codecs=vp9")
                            ? "video/webm; codecs=vp9"
                            : "video/webm";

                        let mediaRecorder = new MediaRecorder(stream, { mimeType: mime });
                        let chunks = [];

                        // Event listener for data available
                        mediaRecorder.addEventListener('dataavailable', function (e) {
                            chunks.push(e.data);
                        });

                        // Event listener for recording stop
                        mediaRecorder.addEventListener('stop', function () {
                            // Change button color back to default
                            let icon = document.querySelector(".record");
                            icon.style.color = 'white';

                            // Create a blob from the recorded chunks
                            let blob = new Blob(chunks, { type: chunks[0].type });

                            // Convert blob to base64
                            const blobToBase64 = blob => {
                                const reader = new FileReader();
                                reader.readAsDataURL(blob);
                                return new Promise(resolve => {
                                    reader.onloadend = () => {
                                        resolve(reader.result);
                                    };
                                });
                            };

                            // Process the base64 result
                            blobToBase64(blob).then(res => {
                                // Send the base64 data to the Odoo server
                                rpc.query({
                                    model: 'video.store',
                                    method: 'video_record',
                                    args: [res],
                                }).then(function (response) { });
                            });
                        });

                        // Start recording
                        mediaRecorder.start();
                    })
                    .catch(error => {
                        console.error('Error capturing screen:', error);
                        // Handle error as needed
                    });
            } catch (e) {
                console.error('Error:', e);
                // Handle error as needed
            }
        },
    });
    SystrayMenu.Items.push(VideoButton);
    return VideoButton;
});
