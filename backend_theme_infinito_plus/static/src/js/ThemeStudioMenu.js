/** @odoo-module */
/**
 * Applies a patch to extend the functionality of the EditorClientAction class.
 * Overrides the _onResetClick method to include additional actions when resetting styles.
 */
import { patch } from "@web/core/utils/patch";
import { EditorClientAction } from '@backend_theme_infinito/js/editor_client_action';
import { jsonrpc } from "@web/core/network/rpc_service";
patch(EditorClientAction.prototype, {
     /**
     * Overrides the default behavior of the reset click event.
     * Triggers additional actions to reset styles to default.
     * @returns {void}
     */
    _onResetClick(){
        super._onResetClick(...arguments);
        jsonrpc('/theme_studio_plus/reset_to_default_style', {
             method:'call'
        });
    },
});

