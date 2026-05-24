/** @odoo-module **/

/**
 * Extends Many2ManyTagsFieldColorEditable to:
 * - Show dialog on tag click
 * - Allow copying tag text
 * - Open form view of selected record
 */

import { _t } from "@web/core/l10n/translation";
import { useService } from "@web/core/utils/hooks";
import { Many2ManyTagsFieldColorEditable } from "@web/views/fields/many2many_tags/many2many_tags_field";
import { patch } from "@web/core/utils/patch";
import { ConfirmationDialog } from "@web/core/confirmation_dialog/confirmation_dialog";

patch(Many2ManyTagsFieldColorEditable.prototype, {
    setup() {
        /**
         * Initializes the component and loads required services.
         *
         * Services:
         * - notification: Displays success/error messages to the user.
         * - action: Triggers backend actions (e.g., opening form views).
         * - dialog: Handles dialog rendering and interactions.
         */
        super.setup();
        this.notification = useService("notification");
        this.action = useService("action");
        this.dialogService = useService("dialog");
    },
    onTagClick(ev, record) {
        /**
         * Handles click event on a many2many tag.
         *
         * Opens a confirmation dialog with options to:
         * - Copy the tag text to clipboard.
         * - Open the form view of the selected record.
         *
         */
        const copyText = ev.target.innerText;
        this.dialogService.add(ConfirmationDialog, {
            body: _t("Click 'Copy Text' to copy the value or 'Open Form View' to view the record."),
            confirmClass: "btn-primary",
            confirmLabel: _t("Copy Text"),
            confirm: async () => {
                try {
                    await navigator.clipboard.writeText(copyText);
                    this.notification.add(
                        _t("Copied the text: %s").replace("%s", copyText),
                        { type: "success" }
                    );
                } catch (error) {
                    this.notification.add(_t("Failed to copy text"), {
                        type: "danger",
                    });
                }
            },
            openFormViewLabel: _t("Open Form View"),
            close: true,
            resId: record.resId,
            resModel: record.resModel,
            cancelLabel: _t("Cancel"),
        });
    }
})