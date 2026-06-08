/** @odoo-module */
import { Wysiwyg } from "@html_editor/wysiwyg";
import { EasyChatGPTDialog } from "./EasyChatGPTDialog";
import { patch } from "@web/core/utils/patch";
import { useEffect } from "@odoo/owl";

patch(Wysiwyg.prototype, {
    setup() {
        super.setup();
        useEffect((openPrompt) => {
            if (openPrompt) {
                this.openChatGPTDialog()
            }
        }, () => [this.props.config?.openPrompt])
    },

    openChatGPTDialog() {
        // In Odoo 19, many properties are handled by the editor instance
        const params = {
            insert: (fragment) => {
                this.editor.shared.dom.insert(fragment);
            },
            sanitize: (node, options) => this.editor.shared.sanitize.sanitize(node, options),
        };

        if (this.props.config.systray) {
            params.systray = this.props.config.systray
        }

        this.env.services.dialog.add(
            EasyChatGPTDialog,
            params
        );
    }
});
