odoo.define('chatter_camera.camera_chatter', function(require) {
    "use strict";
    const components = {
        ChatterTopbar: require('mail/static/src/components/chatter_topbar/chatter_topbar.js'),
    };
    const rpc = require('web.rpc');
    const {patch} = require('web.utils');
    patch(components.ChatterTopbar, 'mail/static/src/models/chatter/chatter.js', {
        /**
         * Open the camera
         **/
        onClickCamera(ev) {
            var myModal = $(ev.target.parentElement.nextSibling.childNodes[0]);
            myModal[0].style.display = "block";
            var All_mediaDevices = navigator.mediaDevices;
            All_mediaDevices.getUserMedia({
                    audio: false,
                    video: true
                })
                .then(function(vidStream) {
                    var video = document.getElementById('videoCam');
                    if ("srcObject" in video) {
                        video.srcObject = vidStream;
                    } else {
                        video.src = window.URL.createObjectURL(vidStream);
                    }
                    video.onloadedmetadata = function(e) {
                        video.play();
                    };
                })
        },
        /**
         * Capture the image
         **/
        async onClickStop(ev){
            var myModal = $(ev.target.parentElement.parentElement.parentElement);
            myModal[0].style.display = "none";
            window.location.reload();
        },
        async ImageCapture() {
            var canvas = document.querySelector("#canvas");
            var video = document.querySelector("#videoCam");
            canvas.getContext('2d').drawImage(video, 0, 0, canvas.width, canvas.height);
            var image_data_url = canvas.toDataURL();
            const children = this.__owl__.children;
            for (const [key, value] of Object.entries(children)) {
                var threadLocalId = value.props.threadLocalId;
            }
            const Match = threadLocalId.split('_');
            image_data_url=image_data_url.replace(/^data:image\/\w+;base64,/, "");
            var query = await rpc.query({
                model: 'ir.attachment',
                method: 'chatter_image',
                args: [Match[1], Match[2], image_data_url]
            }).then(function() {
                location.reload();
            });
        }
    });
});