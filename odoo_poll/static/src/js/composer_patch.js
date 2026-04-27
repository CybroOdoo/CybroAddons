/** @odoo-module **/

import { Composer } from "@mail/core/common/composer";
import { patch } from "@web/core/utils/patch";
import { useService } from "@web/core/utils/hooks";
import { registry } from "@web/core/registry";

/**
 * Patch the Composer component to add the Poll button.
 * PollDialog is accessed via the registry to avoid dynamic import issues.
 */
patch(Composer.prototype, {
    setup() {
        super.setup(...arguments);
        this.pollDialogService = useService("dialog");
    },

    onClickPollButton(ev) {
        ev.preventDefault();
        ev.stopPropagation();

        // Get PollDialog from registry (registered in poll_dialog.js)
        const PollDialog = registry.category("discuss.poll_components").get("PollDialog");

        if (!PollDialog) {
            console.error("PollDialog not found in registry.");
            return;
        }

        // Safely get thread from Odoo 18 composer props
        // Try multiple ways as internal API may vary
        let threadId, threadModel;

        if (this.props.thread) {
            threadId = this.props.thread.id;
            threadModel = this.props.thread.model;
        } else if (this.props.composer && this.props.composer.thread) {
            threadId = this.props.composer.thread.id;
            threadModel = this.props.composer.thread.model;
        } else {
            // Fallback: search in component tree
            console.warn("Poll: Could not find thread in composer props.", this.props);
            return;
        }

        this.pollDialogService.add(PollDialog, {
            threadId: threadId,
            threadModel: threadModel,
            onPollCreated: () => {
                // Poll created successfully
            },
        });
    },
});
