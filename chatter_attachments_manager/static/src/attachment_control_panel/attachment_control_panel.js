/** @odoo-module **/
import { AttachmentBox } from '@mail/components/attachment_box/attachment_box';
import { patch } from 'web.utils';
import Dialog from 'web.Dialog';
import view_dialogs from 'web.view_dialogs';
import core from 'web.core';
import rpc from 'web.rpc';
const { useRef } = owl;
const _t = core._t;

patch(AttachmentBox.prototype, 'chatter_attachments_manager_attachment_box', {
    //--------------------------------------------------------------------------
    // Handlers
    //--------------------------------------------------------------------------
    setup() {
   this._super.apply(this, arguments);
   this.MyModal = useRef('myModal')
   this.control_menu = useRef('control_menu_dropdown')
   },
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
        console.log(e.name + ": " + e.message);
    });
    }
});
