/** @odoo-module **/

import { AbstractFieldBinary } from "web.basic_fields";
import Dialog from 'web.Dialog';
import { qweb as QWeb, _t } from 'web.core';
import rpc from 'web.rpc';
AbstractFieldBinary.include({
    events:  _.extend({}, AbstractFieldBinary.prototype.events,{
        'click ._image_capture_button':"onFileCamera",
    }),
    init: function (parent, name, record) {
        this._super.apply(this, arguments);
        console.log(this.events)
        this.events['click ._image_capture_button'] = 'onFileCamera'
    },
    onFileCamera:async function (ev) {
        ev.stopPropagation();
        var self=this
        const videoElement = document.createElement('video');
        videoElement.autoplay = true;
        videoElement.playsinline = true;
        const imageElement = document.createElement('img');
        imageElement.style.display = 'none';
        const videoStream = await navigator.mediaDevices.getUserMedia({ audio: false, video: true });
        if ('srcObject' in videoElement) {
            videoElement.srcObject = videoStream;
        } else {
            videoElement.src = window.URL.createObjectURL(videoStream);
        }
        var save = function () {
            this.$content.srcObject.getVideoTracks().forEach((track) => {
                track.stop();
            });
            const video = this.$content
            const canvas = document.createElement("canvas");
            canvas.width = video.videoWidth;
            canvas.height = video.videoHeight;
            const canvasContext = canvas.getContext("2d");
            canvasContext.drawImage(video, 0, 0);
            this.img=canvas.toDataURL('image/jpeg');
            this.img_binary = this.img.split(',')[1]
            video.src = this.img
            self._update_image(this.img_binary)
        }
        new Dialog(this, {
            title: _t('Camera'),
            $content: videoElement,
            buttons: [{
                text: _t('Click & Save'),
                classes: 'btn-primary',
                close: true,
                click:save,
            },
            {
                text:_t("cancel"),
                close:true,
                click:this._close,
            }
            ],
        }).open();
    },
    _close:function(){
        this.$content.srcObject.getVideoTracks().forEach((track) => {
                track.stop();
        });
    },
    _update_image:function(img_binary){
        let values = {}
        values[this.name] = img_binary
        rpc.query({
            model:this.model,
            method:'write',
            args:[[this.res_id],values]
        })
        window.location.reload();
    }
})
