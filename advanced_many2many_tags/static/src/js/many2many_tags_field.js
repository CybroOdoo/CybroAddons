/** @odoo-module **/

import { _t } from "@web/core/l10n/translation";
import { useService } from "@web/core/utils/hooks";
import {
    many2ManyTagsField,
    Many2ManyTagsField,
    Many2ManyTagsFieldColorEditable,
} from "@web/views/fields/many2many_tags/many2many_tags_field";
import { patch } from "@web/core/utils/patch";
import { Dialog } from "@web/core/dialog/dialog";
import { ConfirmationDialog } from "@web/core/confirmation_dialog/confirmation_dialog";

patch(Many2ManyTagsFieldColorEditable.prototype, {
    /*Here Many2ManyTagsFieldColorEditable is patched to over ride onBadgeClick()*/
    setup() {
        super.setup();
        this.notification = useService("notification");
        this.action = useService("action");
        this.dialogService = useService("dialog");
    },
    onBadgeClick(ev, record) {
        /*This function is override to open a dialog box on click of
        many2many field and the value is copied if copy button is clicked .
        If open form view is clicked then form view of the field is opened.*/
        var copytext = ev.target.innerText;
        var buttons = [
            {
                text: _t("Ok"),
                classes: 'btn-primary',
                close: true,
            },
        ];
        this.dialogService.add(ConfirmationDialog, {
            body: _t("If you want to copy text click 'Copy Text'. If you want to open form view click 'Open Form View'."),
            confirmClass: "btn-primary",
            confirmLabel: _t("Copy Text"),
            confirm: () => {
                // Create a temporary textarea element
                let textarea = document.createElement('textarea');
                textarea.value = copytext;
                // Make the textarea invisible and add it to the document
                textarea.style.position = 'fixed';
                textarea.style.opacity = 0;
                document.body.appendChild(textarea);
                // Select the text in the textarea and copy it to the clipboard
                textarea.select();
                document.execCommand('copy');
                // Remove the textarea from the document
                document.body.removeChild(textarea);
                // Show a success notification
                this.notification.add(_t("Copied the text: " + copytext), {
                    type: "success",
                });
            },
            open_form_viewClass: "btn-primary",
            open_form_viewLabel: _t("Open Form View"),
            close: true,
            recordResId: record.resId,
            cancelLabel: _t("Cancel"),
            cancel: () => {},
        });
    }
})