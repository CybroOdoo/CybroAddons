odoo.define('image_capture_upload_widget.image_upload', function (require) {
"use strict";
    const FormController = require('web.FormController');
    const FormView = require('web.FormView');
    const viewRegistry = require('web.view_registry');
    var rpc = require('web.rpc');
    var core = require('web.core');
    var Dialog = require('web.Dialog');
    var _t = core._t;
    var data
    var url
    const CaptureWizardFormRenderer = FormController.extend({
    custom_events: _.extend({}, FormController.prototype.custom_events, {
        button_clicked: 'OnClickOpenCamera',
    }),
     init: function () {
             this._super.apply(this, arguments);
                const self = this;
                data=this.initialState.context
     },
       renderButtons: function ($node) {
        this._super.apply(this, arguments);
        // When clicking on "Add", create a new record in form view
        this.$buttons.on('click', '.camera', this.OnClickOpenCamera);
        this.$buttons.on('click', '.capture', this.OnClickCaptureImage);
        this.$buttons.on('click', '.save_image', this.OnClickSaveImage);
    },
OnClickOpenCamera: async function () {
    // opening the camera for capturing the image
    var player = document.getElementById('player');
    var captureButton = document.getElementById('capture');
    var camera = document.getElementById('camera');
    player.classList.remove('d-none');
    captureButton.classList.remove('d-none');
    camera.classList.add('d-none');
    // Check if the browser supports getUserMedia
    if (navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {
        // Request access to the video stream
        await navigator.mediaDevices.getUserMedia({ video: true, audio: false })
            .then(function (stream) {
                // Success callback, stream is a MediaStream object
                player.srcObject = stream;
            })
            .catch(function (error) {
            });
    } else {
        Dialog.alert(self, _t('getUserMedia is not supported in this browser.'))
    }
},
OnClickCaptureImage: function() {
        // Capture the image from webcam and close the webcam
        var context = snapshot.getContext('2d');
        var canvas = document.getElementById('snapshot')
        var save_image = document.getElementById('save_image')
        var image = document.getElementById('image');
        var video = document.getElementById('video')
        var camera = document.getElementById('camera');
        save_image.classList.remove('d-none');
        context.drawImage(player, 0, 0, 300, 200);
        image.value = context.canvas.toDataURL();
        canvas.classList.remove('d-none');
        url = context.canvas.toDataURL()
    },
    OnClickSaveImage: function(){
        rpc.query({
            model: 'image.capture',
            method: 'action_save_image',
            args: [[], data, url],
        }).then(function(results){
            location.reload();
        })
    }
});
 const CaptureView = FormView.extend({
        config: _.extend({}, FormView.prototype.config, {
            Controller: CaptureWizardFormRenderer,
        }),
    });
    viewRegistry.add('capture_wizard', CaptureView);
    return CaptureView;
});
