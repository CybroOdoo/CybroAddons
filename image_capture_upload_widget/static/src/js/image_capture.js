odoo.define('image_capture_upload_widget.CaptureImage', function (require) {
    "use strict";
        const { getDataURLFromFile } = require('web.utils');
    var basicFields =require('web.basic_fields');
    var rpc = require('web.rpc');
    var core = require('web.core');
    var fieldRegistry = require('web.field_registry');
    const toBase64 = file => new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.readAsDataURL(file);
    reader.onload = () => resolve(reader.result);
    reader.onerror = error => reject(error);
});
    var QWeb = core.qweb;
    var CaptureImage = basicFields.FieldBinaryImage.extend({
        template: 'CaptureImage',
        events: {
            'click .o_select_file_button': 'onFileEdit',
            'click .o_upload_image_button': 'onFileUpload',
            'click .o_clear_file_button': 'onFileClear'
        },
        onFileEdit: function (ev) {
    var self = this;
    // Create an input element of type file
    var fileInput = document.createElement('input');
    fileInput.type = 'file';
    // Trigger the file selection dialog
    fileInput.click();
    // Handle the selected file
fileInput.addEventListener('change', async function (event) {
        var file = event.target.files[0];
        if (file) {
            // Perform necessary operations with the selected file
            var file_image = file_splice.split(',')[1]
            //var file_name = ev.target.files[0].name
            var record=rpc.query({
                    model: self.model,
                    method: 'write',
                    args: [[self.res_id], {[self.name] : file_image }],
                }).then(function(){
            window.location.reload();
                       });
            // You can also upload the file to the server if needed
            // Implement the desired functionality for file upload
        }
    });
},
onFileClear: function (ev) {
    var self = this;
            rpc.query({
                    model: self.model,
                    method: 'write',
                    args: [[self.res_id], {[self.name] : 0 }],
                }).then(function(){
            window.location.reload();
                       });
},
onFileUpload: function (ev) {
    ev.preventDefault();
    var self = this;
    // Open form using do_action
    var action = {
        type: 'ir.actions.act_window',
        res_model: 'image.capture',
        views: [[false, 'form']],
        target: 'new',  // Open the form in a new window/tab
        context: {'model_name': self.model, 'record_id': self.res_id, 'field_name': self.name}
    };
    this.do_action(action);
        },
    });
fieldRegistry.add('capture_image', CaptureImage);
    return CaptureImage;
});
