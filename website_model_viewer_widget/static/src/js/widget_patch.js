/** @odoo-module **/

import { patch } from "@web/core/utils/patch";
import { Field3D } from "@model_viewer_widget/js/widget";
import { url } from "@web/core/utils/urls";
import { useService } from "@web/core/utils/hooks";
import { useEffect } from "@odoo/owl";

patch(Field3D.prototype, {
    setup() {
        super.setup();
        this.notification = useService("notification");
        useEffect(() => {
            if (this.view3D) {
                // Ensure we handle load errors in the backend widget too
                this.view3D.off("loadError"); // Avoid multiple listeners if patched multiple times
                this.view3D.on("loadError", (e) => {
                    console.error("View3D load error:", e.message);
                    const defaultUrl = url('/model_viewer_widget/static/src/assets/3d.glb');
                    if (this.state.value !== defaultUrl) {
                        this.state.value = defaultUrl;
                        this.view3D.load(this.state.value);
                    }
                });
            }
        });
    },

    async onFileUploaded(info) {
        if (info.name && !info.name.toLowerCase().endsWith(".glb")) {
            this.notification.add("Invalid file format. Please upload a .glb file.", {
                title: "Upload Error",
                type: "danger",
            });
            return;
        }
        await super.onFileUploaded(info);
    }
});

Field3D.acceptedFileExtensions = ".glb,.gltf";
