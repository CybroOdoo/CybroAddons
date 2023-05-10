/** @odoo-module */

import { registry } from '@web/core/registry';

import { formView } from '@web/views/form/form_view';
import { FormController } from '@web/views/form/form_controller';
import { FormRenderer } from '@web/views/form/form_renderer';
const { useListener } = require("@web/core/utils/hooks");
import rpc from 'web.rpc';
import { patch } from "@web/core/utils/patch";

patch(FormRenderer.prototype, 'FormRender',{
    setup() {
        this._super();
    },
    async OnClickOpenCamera() {
        // opening the camera for capture the image
        var player = document.getElementById('player');
        var captureButton = document.getElementById('capture');
        var camera = document.getElementById('camera');
        player.classList.remove('d-none');
        captureButton.classList.remove('d-none');
        camera.classList.add('d-none');
        let stream = await navigator.mediaDevices.getUserMedia({ video: true, audio: false });
	    player.srcObject = stream;
    },
    async OnClickCaptureImage() {
        // Capture the image from webcam and close the webcam
        var context = snapshot.getContext('2d');
        var canvas = document.getElementById('snapshot')
        var save_image = document.getElementById('save_image')
        var image = document.getElementById('image');
        var video = document.getElementById('video')
        var camera = document.getElementById('camera');
        save_image.classList.remove('d-none');
        context.drawImage(player, 0, 0, 320, 240);
        image.value = context.canvas.toDataURL();
        canvas.classList.remove('d-none');
        this.url = context.canvas.toDataURL()
    },
    async OnClickSaveImage(){
        // Saving the image to that field
        rpc.query({
            model: 'image.capture',
            method: 'action_save_image',
            args: [[], this.props.record.data, this.url],
        }).then(function(results){
            location.reload();
        })
    }
});
