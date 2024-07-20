/** @odoo-module **/
import { AttachmentBox } from '@mail/components/attachment_box/attachment_box';
import { patch } from 'web.utils';
import Dialog from 'web.Dialog';
import view_dialogs from 'web.view_dialogs';
import core from 'web.core';
import rpc from 'web.rpc';
const { useRef,onWillUnmount,onMounted , useState} = owl.hooks;
const _t = core._t;

patch(AttachmentBox.prototype, 'chatter_attachments_manager_attachment_box', {
    setup() {
        this._super.apply(this, arguments);
        this.MyModal = useRef('myModal');
        this.control_menu = useRef('control_menu_dropdown');
        this._onClickGlobal = this._onClickGlobal.bind(this)
        this.state = useState({
            isDropdownOpen: false,
        });
        onMounted(() => {
            document.addEventListener('click', this._onClickGlobal)
        })
        onWillUnmount(() => {
            document.removeEventListener('click', this._onClickGlobal)
        })
    },

    _onClickGlobal(ev){
    //----To close the dropdown on outside click
        if(this.state?.isDropdownOpen && !this.control_menu.el.contains(ev.target)){
            this.state.isDropdownOpen = false
        }
    },

    onClickUpload(){
    //----Open a dropdown on click upload icon
        this.state.isDropdownOpen = !this.state.isDropdownOpen
    },

    onClickCamera(ev) {
    //----Open camera to capture
        if (this.control_menu.el.style.display === "none") {
            this.control_menu.el.style.display = "block";
        }
        else {
            this.control_menu.el.style.display = "none";
        }
        var self = this;
        this.MyModal.el.style.display = "table";
        let All_mediaDevices = navigator?.mediaDevices
        All_mediaDevices?.getUserMedia({
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
    },

    ImageCapture: function(){
    //----Capture the image
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
        this._fileUploaderRef.comp.uploadFiles(fl)
    },

    async onClickScreenRec(ev){
    //----Capturing Screen recording
    if (this.control_menu.el.style.display === "none") {
            this.control_menu.el.style.display = "block";
        }
        else {
            this.control_menu.el.style.display = "none";
        }
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
                    self._fileUploaderRef.comp.uploadFiles(fl)
                });
            })
            mediaRecorder.start()
        }
        catch(e){}
    },

    _onClickAddAttachment() {
    //----On clicking add Attachments
    if (this.control_menu.el.style.display === "none") {
            this.control_menu.el.style.display = "block";
        }
        else {
            this.control_menu.el.style.display = "none";
        }
        this._fileUploaderRef.comp.openBrowserFileUploader();
    },

    onClickDownloadAll(ev) {
    //----On clicking Download All button
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
});
