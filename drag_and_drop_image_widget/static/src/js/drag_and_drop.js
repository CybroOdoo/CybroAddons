odoo.define('drag_and_drop_image_widget.drag_and_drop_templates', function (require) {
    "use strict";

var field_registry = require('web.field_registry');
var basicFields = require('web.basic_fields');
var FieldBinaryImage = basicFields.FieldBinaryImage;
/**
 * Odoo widget for drag and drop image upload functionality.
 *
 * This widget extends the FieldBinaryImage widget to handle drag and drop events
 * for uploading images. When an image file is dropped onto the widget area:
 * - It prevents default browser behavior for 'dragover' and 'drop' events.
 * - Reads the dropped file using FileReader to get its base64-encoded content.
 * - Updates the src attribute of the '.img.img-fluid' element with the dropped image.
 * - Calls the Odoo RPC method to asynchronously write the image data to the server.
 *
 */

var DragAndDropBinaryField= FieldBinaryImage.extend({
      start: function () {
            this._super.apply(this, arguments)
        },
/**
 * @listens drop - Handles the drop event when a file is dropped onto the widget.
 * @listens dragover - Prevents default browser behavior for the dragover event.
 */
      events: _.extend({}, FieldBinaryImage.prototype.events, {
            'drop': 'onDropItem',
            'dragover': 'onDragOver',
      }),
    onDragOver: function(ev){
         ev.preventDefault();
    },
    /**
     * Handle drop event for image upload.
     */
    onDropItem: function(ev){
    ev.preventDefault();
    ev.stopPropagation();
    const file = event.dataTransfer.files[0];
    const reader = new FileReader();
        reader.onload = async (e) => {
            const fileContent = e.target.result;
            this.el.querySelector(".img.img-fluid").src = fileContent
            await this._rpc({
              model: this.model,
              method: 'write',
              args: [
                  this.res_id,
                  {
                [this.name] : fileContent.split(",")[1]
              }
              ],
          })
        };
        reader.readAsDataURL(file);
    },
});
field_registry.add('drag_and_drop', DragAndDropBinaryField);
return {
    DragAndDropBinaryField: DragAndDropBinaryField,
}
})
