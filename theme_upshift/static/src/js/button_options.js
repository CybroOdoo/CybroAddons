/** @odoo-module **/

import { Plugin } from "@html_editor/plugin";
import { registry } from "@web/core/registry";
import { withSequence } from "@html_editor/utils/resource";
import { SNIPPET_SPECIFIC } from "@html_builder/utils/option_sequence";

console.log("ButtonOptionPlugin loading...");

class ButtonOptionPlugin extends Plugin {
    static id = "themeUpshiftButtonOption";
    setup() {
        console.log("ButtonOptionPlugin setup");
    }
    resources = {
        builder_options: [
            withSequence(SNIPPET_SPECIFIC, {
                template: "theme_upshift.buttonOption",
                selector: ".btn",
            }),
        ],
    };
}

registry.category("website-plugins").add(ButtonOptionPlugin.id, ButtonOptionPlugin);
