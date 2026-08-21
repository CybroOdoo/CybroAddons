/** @odoo-module **/

import { Plugin } from "@html_editor/plugin";

/**
 * Editor plugin that registers a powerbox command to insert a toggle/collapsible list block.
 */
export class ToggleListPluginCommunity extends Plugin {
    static id = "toggleListCommunity";
    static dependencies = ["userCommand"];

    resources = {
        powerbox_items: [
            {
                commandId: "insertToggleBlock",
                categoryId: "structure",
            },
        ],
    };

    setup() {
    }
}
