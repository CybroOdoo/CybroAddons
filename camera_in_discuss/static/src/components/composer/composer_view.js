/** @odoo-module **/

import { Composer } from '@mail/components/composer/composer';
import { patch } from 'web.utils';

patch(Composer.prototype, 'camera_in_discuss/static/src/components/composer/composer_view.js', {
     async onClickCamera(ev){
        myModal.style.display = "block";
        var video= ev.target.parentElement.querySelector('#videoCam')
        var stopButton = ev.target.parentElement.querySelector('#stop-camera-button')
        let All_mediaDevices=navigator.mediaDevices
            All_mediaDevices.getUserMedia({
            audio: false,
            video: true
        })

        .then(function(vidStream) {
            if ("srcObject" in video) {
               video.srcObject = vidStream;
            } else {
               video.src = window.URL.createObjectURL(vidStream); //video recording section
            }
            video.onloadedmetadata = function(e) {
               video.play();
            };
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

    /** Function for closing the modal **/
    _close_modal: function(){
        myModal.style.display = "none";
    },

    /** Function for Image Capturing through the modal **/
    ImageCapture: function(ev) {
         let canvas = ev.target.offsetParent.querySelector('#canvas');
         let video = ev.target.offsetParent.querySelector('#videoCam');
         canvas.getContext('2d').drawImage(video, 0, 0, canvas.width, canvas.height);
         let image_data_url = canvas.toDataURL('image/jpeg');
         var fl=[];
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

        this._fileUploaderRef.comp.uploadFiles(fl);
        myModal.style.display = "none";
    },

    /** Function for adding the content to the discuss line **/
    onClickSend: function (ev) {
        this.sendMessage();
    }
});
