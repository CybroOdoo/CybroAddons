/** @odoo-module **/

import { patch } from "@web/core/utils/patch";
import { Field3D } from "@model_viewer_widget/js/widget";

patch(Field3D.prototype, {
    async onFileUploaded(info) {
        if (info.name && !info.name.toLowerCase().endsWith(".glb")) {
            this.notification?.add("Invalid file format. Please upload a .glb file.", {
                title: "Upload Error",
                type: "danger",
            });
            return;
        }
        await super.onFileUploaded(info);
    }
});

Field3D.acceptedFileExtensions = ".glb";
