/** @odoo-module */

import { FormLabel } from "@web/views/form/form_label";
import { patch } from "@web/core/utils/patch";
import { rpc } from "@web/core/network/rpc";

patch(FormLabel.prototype, {
    /** Enable inline editing only for users granted the server-side permission. */
    async onDblClick(event) {
        const canEdit = await rpc(`/web/dataset/call_kw/res.users/login_user`, {
            model: "res.users",
            method: "login_user",
            args: [],
            kwargs: {},
        });
        if (!canEdit) {
            return;
        }

        const label = event.target.closest("label") || event.target;
        if (label.localName !== "label") {
            return;
        }

        const input = document.createElement("input");
        input.className = "edit_label";
        input.dataset.labelFor = label.htmlFor;
        input.value = label.innerText;
        input.addEventListener("blur", () => this.updateFieldLabel(input, label));
        label.replaceWith(input);
        input.focus();
    },

    /** Persist the changed label, restoring the label when the RPC is rejected. */
    async updateFieldLabel(input, label) {
        const modelName = this.props.record
            ? (this.props.record.resModel || this.props.record._config?.resModel)
            : "";
        const viewType = this.props.fieldInfo?.viewType || "form";
        const oldLabel = label.innerText;
        const newLabel = input.value;
        const fieldName = this.props.fieldName;
        const labelFor = label.htmlFor;

        try {
            const updated = await rpc(`/web/dataset/call_kw/ir.ui.view/edit_xml_field_label`, {
                model: "ir.ui.view",
                method: "edit_xml_field_label",
                args: [modelName, viewType, oldLabel, labelFor, newLabel, fieldName],
                kwargs: {},
            });
            if (!updated) {
                input.replaceWith(label);
                return;
            }

            label.innerText = newLabel;
            input.replaceWith(label);
            window.location.reload();
        } catch {
            input.replaceWith(label);
        }
    },
});
