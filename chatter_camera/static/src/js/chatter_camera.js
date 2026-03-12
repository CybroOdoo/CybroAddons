/** @odoo-module **/
import { Chatter } from "@mail/chatter/web_portal/chatter";
import { patch } from "@web/core/utils/patch";
import { useRef } from "@odoo/owl";

//patch the class ChatterContainer to added the click function
patch(Chatter.prototype, {
    setup() {
        super.setup();
        this.video = useRef("video");
        this.stop_camera = useRef("stop-camera-button");
        this.canvas = useRef("canvas");
        this.currentStream = null; // Store the current stream
    },

    onClickCamera: function() {
        var self = this;

        // Check if mediaDevices is supported
        if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
            alert('Camera access is not supported in this browser or requires HTTPS connection.');
            console.error('Make sure you are using HTTPS or localhost.');
            return;
        }

        const myModal = document.getElementById('myModal');
        if (!myModal) {
            console.error('Modal element not found');
            return;
        }

        myModal.style.display = "flex";

        navigator.mediaDevices.getUserMedia({
            audio: false,
            video: true
        })
        .then(function(vidStream) {
            self.currentStream = vidStream; // Store the stream

            var video = self.video.el;
            if (!video) {
                console.error('Video element not found');
                return;
            }

            if ("srcObject" in video) {
                video.srcObject = vidStream;
            } else {
                video.src = window.URL.createObjectURL(vidStream);
            }

            video.onloadedmetadata = function(e) {
                video.play();
            };

            // Use querySelector or direct DOM access instead of replaceWith
            var stopButton = self.stop_camera.el;
            if (stopButton) {
                // Remove all previous listeners by cloning
                var newStopButton = stopButton.cloneNode(true);
                stopButton.parentNode.replaceChild(newStopButton, stopButton);

                // Add listener to the new button
                newStopButton.addEventListener('click', function() {
                    if (self.currentStream) {
                        self.currentStream.getTracks().forEach(function(track) {
                            track.stop();
                        });
                        self.currentStream = null;
                    }
                    myModal.style.display = "none";
                });
            }
        })
        .catch(function(e) {
            console.error(e.name + ": " + e.message);
            alert('Unable to access camera: ' + e.message);
            myModal.style.display = "none";
        });
    },

    /**
     * Capture the image
     **/
    ImageCapture: function() {
        let canvas = this.canvas.el;
        let video = this.video.el;

        if (!canvas || !video) {
            console.error('Canvas or video element not found');
            return;
        }

        canvas.getContext('2d').drawImage(video, 0, 0, canvas.width, canvas.height);
        let image_data_url = canvas.toDataURL('image/jpeg');

        var arr = image_data_url.split(',');
        var mime = arr[0].match(/:(.*?);/)[1];
        var bstr = atob(arr[1]);
        var n = bstr.length;
        var u8arr = new Uint8Array(n);

        while (n--) {
            u8arr[n] = bstr.charCodeAt(n);
        }

        var f = new File([u8arr], 'image.jpeg', {
            type: mime
        });

        this.attachmentUploader.uploadFile(f);

        // Stop video stream
        if (this.currentStream) {
            this.currentStream.getTracks().forEach(track => track.stop());
            this.currentStream = null;
        }

        const myModal = document.getElementById('myModal');
        if (myModal) {
            myModal.style.display = "none";
        }
        window.location.reload();

    },
});
