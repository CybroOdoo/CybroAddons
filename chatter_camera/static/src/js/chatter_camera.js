/** @odoo-module **/
import { Chatter } from "@mail/core/web/chatter";
import { patch } from "@web/core/utils/patch";
import { useRef } from "@odoo/owl";

//patch the class ChatterContainer to added the click function
patch(Chatter.prototype ,{
    setup() {
        super.setup();
        this.video = useRef("video");
        this.stop_camera = useRef("stop-camera-button");
        this.canvas = useRef("canvas");
    },
    onClickCamera: function(){
            var self = this;
            myModal.style.display = "block";
            let All_mediaDevices=navigator.mediaDevices
                All_mediaDevices.getUserMedia({
                audio: false,
                video: true
            })
            .then(function(vidStream) {
                var video = self.video.el;
                if ("srcObject" in video) {
                   video.srcObject = vidStream;
                } else {
                   video.src = window.URL.createObjectURL(vidStream);
                }
                video.onloadedmetadata = function(e) {
                   video.play();
                };
                var stopButton = self.stop_camera.el
                stopButton.addEventListener('click', function() {
                  vidStream.getTracks().forEach(function(track) {
                    track.stop();
                     myModal.style.display = "none";
                     canvas.toDataURL();
                  });
                });
            })
            .catch(function(e) {
                console.log(e.name + ": " + e.message);
            });
    },
    /**
    Capture the image
    **/
     ImageCapture: function(){
         let canvas = this.canvas.el
         let video = this.video.el
         canvas.getContext('2d').drawImage(video, 0, 0, canvas.width, canvas.height);
         let image_data_url = canvas.toDataURL('image/jpeg');
         var fl = [];
        var arr = image_data_url.split(','),
            mime = arr[0].match(/:(.*?);/)[1],
            bstr = atob(arr[1]),
            n = bstr.length,
            u8arr = new Uint8Array(n);

        while (n--) {
            u8arr[n] = bstr.charCodeAt(n);
        }
        var f = new File([u8arr], 'image.jpeg', {
            type: mime
        });
        fl.push(f);
        this.attachmentUploader.uploadFile(fl[0])
        myModal.style.display = "none";
    },
});
