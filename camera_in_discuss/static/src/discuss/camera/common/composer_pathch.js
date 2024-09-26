/** @odoo-module **/
import { patch } from "@web/core/utils/patch";
import { useRef } from "@odoo/owl";
import { Composer } from "@mail/core/common/composer";

//the below functionality will help to define the camera division and record the image then store in the db
const composerPatch = {
    onClickCamera: function(ev) { //used for onclick function for the camera
    console.log(ev);
        var self = this
        $('#myModal').modal('show')
        var video = ev.target.parentElement.querySelector('#videoCam')
        var stopButton = ev.target.parentElement.querySelector('#stop-camera-button')
        let All_mediaDevices = navigator.mediaDevices
        All_mediaDevices.getUserMedia({
                audio: false,
                video: true
            })
            .then(function(vidStream) {
                self.vidStream = vidStream
                if ("srcObject" in video) {
                    video.srcObject = vidStream;
                } else {
                    video.src = window.URL.createObjectURL(vidStream); //video recording section
                }
                video.onloadedmetadata = function(e) {
                    video.play();
                };
            })
            .catch(function(e) {
                console.log(e.name + ": " + e.message);
            });
    },
    ImageCapture: async function(ev) {
        let canvas = ev.target.offsetParent.querySelector('#canvas');
        let video = ev.target.offsetParent.querySelector('#videoCam');
        canvas.getContext('2d').drawImage(video, 0, 0, canvas.width, canvas.height);
        let image_data_url = canvas.toDataURL('image/jpeg');
        var fl = {}
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
        await this.attachmentUploader.uploadFile(f)
        this.OnClickCancel()
    },
    OnClickCancel(){
        this.vidStream.getTracks().forEach(function(track) {
            track.stop();
            $('#myModal').modal('hide')
        });
    },
}
patch(Composer.prototype, composerPatch);
