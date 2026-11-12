/** @odoo-module **/

import { Chatter } from "@mail/chatter/web_portal/chatter";
import { ConfirmationDialog } from "@web/core/confirmation_dialog/confirmation_dialog";
import { _t } from "@web/core/l10n/translation";
import { patch } from "@web/core/utils/patch";
import { useService } from "@web/core/utils/hooks";

patch(Chatter.prototype, {
    setup() {
        super.setup(...arguments);
        this.orm = useService("orm");
        this.dialog = useService("dialog");
        this.notification = useService("notification");
    },

    onClickClearMessages() {
        const { threadModel: model, threadId: resId } = this.props;

        if (!model || !resId) {
            return;
        }

        this.dialog.add(ConfirmationDialog, {
            title: _t("Clear Chatter Messages"),
            body: _t(
                "Are you sure you want to delete all chatter messages from this record? " +
                "This action cannot be undone."
            ),
            confirmLabel: _t("Clear Messages"),
            cancelLabel: _t("Cancel"),

            confirm: async () => {
                try {
                    const result = await this.orm.call(
                        "mail.thread",
                        "action_clear_chatter_messages",
                        [model, resId]
                    );

                    if (result === true) {
                        this.notification.add(
                            _t("Chatter messages cleared."),
                            { type: "success" }
                        );
                        window.location.reload();
                    } else {
                        this.notification.add(
                            _t("You are not allowed to clear chatter messages."),
                            { type: "danger" }
                        );
                    }
                } catch {
                    this.notification.add(
                        _t("An error occurred while clearing chatter messages."),
                        { type: "danger" }
                    );
                }
            },
        });
    },

});