/** @odoo-module **/
import { registerPatch } from '@mail/model/model_core';

registerPatch({
    name: 'AttachmentBoxView',
    recordMethods: {
         /**
        Capture the image
        **/
         ImageCapture: function(){
            let canvas =  document.querySelector("#canvas");
            let video = document.querySelector("#videoCam");
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
            this.fileUploader.uploadFiles(fl)
        },
         /**
        Record the screen.
        **/
    async onClickScreenRec(ev){
         try {
       let stream = await navigator.mediaDevices.getDisplayMedia({
            video: true
        })
        const mime = MediaRecorder.isTypeSupported("video/webm; codecs=vp9")
                 ? "video/webm; codecs=vp9"
                 : "video/webm"
        let mediaRecorder = new MediaRecorder(stream, {
            mimeType: mime
        })
        var self = this;
        let chunks = []
        mediaRecorder.addEventListener('dataavailable', function(e) {
            chunks.push(e.data)
        })
        mediaRecorder.addEventListener('stop', function(){
            let blob = new Blob(chunks, {
                type: chunks[0].type
            })
             const blobToBase64 = blob => {
              const reader = new FileReader();
              reader.readAsDataURL(blob);
              return new Promise(resolve => {
                reader.onloadend = () => {
                  resolve(reader.result);
                };
              });
            };
            blobToBase64(blob).then(res => {
            var fl = [];
               var arr = res.split(','),
                mime = arr[0].match(/:(.*?);/)[1],
                bstr = atob(arr[1]),
                n = bstr.length,
                u8arr = new Uint8Array(n);
            while (n--) {
                u8arr[n] = bstr.charCodeAt(n);
            }
            var f = new File([u8arr], 'example.webm', {
                type: mime
            });
            fl.push(f);
            self.fileUploader.uploadFiles(fl)
            });
        })
        mediaRecorder.start()
        } catch(e){}
   },
        /**
        Download all attachments attached to the record.
        **/
    onClickDownloadAll(ev) {
      var apiUrl = '/web/binary/download_document'; // URL of Odoo controller
      var modelName = this.chatter.thread.model;
      var tabId = this.chatter.thread.id;
      fetch(apiUrl + '?param1=' + modelName + '&param2=' + tabId, {
        method: 'GET',
        responseType: 'blob'
      })
      .then(response => response.blob())
      .then(blob => {
        var url = window.URL.createObjectURL(blob);
        var a = $('<a>', {
          style: 'display: none',
          href: url,
          download: modelName + '.zip'
        });
        $('body').append(a);
        a[0].click();
        a.remove();
        window.URL.revokeObjectURL(url);
      })
      .catch(error => {
        console.error('Error downloading zip:', error);
      });
    },
    }
});
