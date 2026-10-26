/** @odoo-module **/
import { _t } from "@web/core/l10n/translation";
import { useService } from "@web/core/utils/hooks";
import { Many2ManyTagsField } from "@web/views/fields/many2many_tags/many2many_tags_field";
import { patch } from "@web/core/utils/patch";
import { ConfirmationDialog } from "@web/core/confirmation_dialog/confirmation_dialog";

patch(Many2ManyTagsField.prototype, {
    /* Here Many2ManyTagsField is patched to override tag click behavior */
    setup() {
        super.setup();
        this.notification = useService("notification");
        this.action = useService("action");
        this.dialogService = useService("dialog");
    },
    onTagClick(ev, record) {
        /* This function is overridden to open a dialog box on click of
        many2many field tag where text can be copied or form view opened. */
        const copyText = (record && record.data && record.data.display_name) || (ev.target && ev.target.innerText) || "";
        this.dialogService.add(ConfirmationDialog, {
            body: _t("If you want to copy text click 'Copy Text'. If you want to open form view click 'Open Form View'."),
            confirmClass: "btn-primary",
            confirmLabel: _t("Copy Text"),
            confirm: async () => {
                if (navigator.clipboard && navigator.clipboard.writeText) {
                    await navigator.clipboard.writeText(copyText);
                }
                this.notification.add(_t("Copied the text: %s", copyText), {
                    type: "success",
                });
            },
            openFormViewClass: "btn-primary",
            openFormViewLabel: _t("Open Form View"),
            resModel: this.relation,
            recordResId: record.resId,
            cancelLabel: _t("Cancel"),
            cancel: () => {},
        });
    }
});

