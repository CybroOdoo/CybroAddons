/** @odoo-module **/

import { ImageField } from '@web/views/fields/image/image_field';
import { patch } from "@web/core/utils/patch";
import { CameraDialog } from "./camera_dialog.js";
import { useService } from "@web/core/utils/hooks";
 /**
 * Updates ImageField
 */
patch(ImageField.prototype, '/capture_image_field/static/src/js/image_upload.js', {
    setup(){
        this._super.apply(this, arguments)
        this.dialogService = useService('dialog')
    },
    onFileCamera(ev){
        ev.stopPropagation()
        this.dialogService.add(CameraDialog, {parent: this},);
    }
})