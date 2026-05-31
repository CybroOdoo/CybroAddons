/** @odoo-module **/

import { ImageField } from '@web/views/fields/image/image_field';
import { patch } from "@web/core/utils/patch";
import { CameraDialog } from "./CameraDialog.js";
import { useService } from "@web/core/utils/hooks";
 /**
 * Updates ImageField
 */
patch(ImageField.prototype,{
    setup(){
        super.setup();
        this.dialogService = useService('dialog')
    },
    onFileCamera(ev){
        ev.stopPropagation()
        this.dialogService.add(CameraDialog, {parent: this},);
    }
})
