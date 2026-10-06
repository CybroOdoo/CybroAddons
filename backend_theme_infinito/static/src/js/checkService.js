/** @odoo-module **/
import { registry } from "@web/core/registry";

export const EditorService = {
    dependencies: ["action"],
    start(env, { action }) {
        return {
            open() {
                return action.doAction({
                    type: "ir.actions.client",
                    tag: "backend_theme_infinito.editor_client_action",
                    target: "current",
                });
            },
        };
    },
};

registry.category("services").add("editor", EditorService);
