/** @odoo-module **/

import { HtmlField } from "@html_editor/fields/html_field";
import { ExcalidrawPlugin } from "./excalidraw_plugin";
import { patch } from "@web/core/utils/patch";

patch(HtmlField.prototype, {
    getConfig() {
        const config = super.getConfig();
        // Add ExcalidrawPlugin to the Plugins list
        config.Plugins.push(ExcalidrawPlugin);
        return config;
    },
});
