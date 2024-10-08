/** @odoo-module **/
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
const { onMounted, mount } = owl
import { EditorClientAction } from "./editor_client_action"
/**
 * EditorService module for managing editor-related functionality.
 */
export const EditorService = {
    /**
     * Starts the EditorService.
     * @param {Object} env - The environment object.
     * @returns {Object} An object containing methods to interact with the editor.
     */
    async start(env) {
        /**
         * Retrieves the current editor action.
         * @returns {Object|null} The current editor action or null if not available.
         */
        function _getCurrentAction() {
            return currentController ? currentController.action : null;
        }
         /**
         * Opens the editor.
         */
        async function open() {
            const currentController = env.services.action.currentController;
            env.services.action.doAction({
                type: "ir.actions.client",
                tag: "backend_theme_infinito.editor_client_action",
                target: "current",
            });
        }
        return {
            open
        };
    },
};

registry.category("services").add("editor", EditorService);

