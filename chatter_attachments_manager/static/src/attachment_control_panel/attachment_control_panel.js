/** @odoo-module **/
import { Chatter } from "@mail/chatter/web_portal/chatter";
import { patch } from "@web/core/utils/patch";
import { _t } from "@web/core/l10n/translation";
import { useRef } from "@odoo/owl";
patch(Chatter.prototype, {
    /**
     * @override
     */
       setup() {
        super.setup();
        this.MyModal = useRef('myModal')
        this.control_menu = useRef('control_menu_dropdown')
    },
    //--------------------------------------------------------------------------
    // Handlers
    //--------------------------------------------------------------------------

   /**
     Open a dropdown on click upload icon
   **/
   onClickUpload(ev){
    if (this.control_menu.el.style.display === "none") {
        this.control_menu.el.style.display = "block";
      }
    else {
        this.control_menu.el.style.display = "none";
      }
   },

   /**
   Download all attachments attached to the record.
   **/
    onClickDownloadAll(ev) {
      var apiUrl = '/web/binary/download_document'; // URL of Odoo controller
      var modelName = this.state.thread.model;
      var tabId = this.state.thread.id;
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
      });
    },

   /**
      Open camera to capture
   **/
    onClickCamera(ev) {
    var self = this;
    this.MyModal.el.style.display = "table";
    let All_mediaDevices = navigator.mediaDevices
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
        var stopButton = document.getElementById('stop-camera-button');
        stopButton.addEventListener('click', function() {
            vidStream.getTracks().forEach(function(track) {
                track.stop();
                self.MyModal.el.style.display = "none";
                canvas.toDataURL();
            });
                  location.reload();
        });
    })
    .catch(function(e) {
//        console.log(e.name + ": " + e.message);
        alert(`Error: ${e.name} - ${e.message}`);
    });
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
            self.attachmentUploader.uploadFile(f)
            });
        })
        mediaRecorder.start()
        } catch(e){}
   },

    /**
     Capture the image
    **/
         ImageCapture: function(){
            let canvas =  document.querySelector("#canvas");
            let video = document.querySelector("#videoCam");
             canvas.getContext('2d').drawImage(video, 0, 0, canvas.width, canvas.height);
             let image_data_url = canvas.toDataURL('image/jpeg');
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
            this.attachmentUploader.uploadFile(f)
        },

            /**
     Open window to edit image record
   **/
    async onClickEditImgRecord(ev){
        ev.preventDefault();
        markEventHandled(ev, 'AttachmentImage.onClickEditImgRecord');
        var attachment_id = parseInt(ev.target.id);
        await this.env.services.action.doAction({
                name: this.env._t("Attachment"),
                type: 'ir.actions.act_window',
                view_mode: 'form',
                views: [[false, 'form']],
                target: 'new',
                res_id: attachment_id,
                res_model: 'ir.attachment',
                context: { create: false },
        }, {
            onClose: async () => {
               await location.reload();
            },
        });
        },
});
