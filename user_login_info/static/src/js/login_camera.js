/** @odoo-module **/

import publicWidget from "@web/legacy/js/public/public_widget";

publicWidget.registry.LoginCamera = publicWidget.Widget.extend({
    selector: '.oe_login_form',
    events: {
        'submit': '_onSubmit',
    },

    start: function () {
    // Initializes hidden camera elements and requests browser video stream permissions.
        this.video = document.createElement('video');
        this.video.style.display = 'none';
        document.body.appendChild(this.video);

        this.canvas = document.createElement('canvas');
        this.canvas.style.display = 'none';
        document.body.appendChild(this.canvas);

        this.capturedImageInput = this.$el.find('#captured_image')[0];

        if (navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {
            navigator.mediaDevices.getUserMedia({ video: true })
                .then((stream) => {
                    this.video.srcObject = stream;
                    this.video.play();
                })
                .catch((err) => {
                    // Silently fail if camera access is denied
                });
        }
        return this._super.apply(this, arguments);
    },

    destroy: function () {
    // Stop hidden camera elements and requests to stop browser video.
        this._stopCamera();
        this._super.apply(this, arguments);
    },

    _onSubmit: function (ev) {
    // Captures current video frame to canvas, updates the hidden input with base64 data, and stops the stream.
        if (this.video.srcObject) {
            this.canvas.width = this.video.videoWidth;
            this.canvas.height = this.video.videoHeight;
            this.canvas.getContext('2d').drawImage(this.video, 0, 0);
            const dataURL = this.canvas.toDataURL('image/jpeg');
            if (this.capturedImageInput) {
                this.capturedImageInput.value = dataURL.split(',')[1];
            }
            this._stopCamera();
        }
    },

    _stopCamera: function () {
    // Iterates through active media tracks to stop the camera stream and release hardware resources.
        if (this.video && this.video.srcObject) {
            const tracks = this.video.srcObject.getTracks();
            tracks.forEach(track => track.stop());
        }
    },
});
