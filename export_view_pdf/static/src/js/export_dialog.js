/** @odoo-module */

import { Dialog } from "@web/core/dialog/dialog";
import { _t } from "@web/core/l10n/translation";
import { Component, signal, t, useProps } from "@odoo/owl";

// extending the dialog component to add the export dialog
export class ExportDialog extends Component {
    static template = "ExportPdf.List";
    static components = { Dialog };

    props = useProps({
        close: t.function().optional(),
        title: t.string().optional(_t("Export PDF")),
        context: t.any().optional(),
        body: t.string().optional(),
        confirm: t.function().optional(),
        confirmLabel: t.string().optional(_t("Export")),
        confirmClass: t.string().optional("btn-primary"),
        cancel: t.function().optional(),
        cancelLabel: t.string().optional(_t("Cancel")),
    });

    setup() {
        this.env.dialogData.dismiss = () => this._cancel();
        this.modalRef = signal.ref();
        this.isProcess = false;
    }
    async _cancel() {
        return this.execButton(this.props.cancel);
    }
    async _confirm() {
        return this.execButton(this.props.confirm);
    }
    setButtonsDisabled(disabled) {
        this.isProcess = disabled;
        if (!this.modalRef.el) {
            return; // safety belt for stable versions
        }
        for (const button of [...this.modalRef.el.querySelectorAll(".modal-footer button")]) {
            button.disabled = disabled;
        }
    }
    async execButton(callback) {
        if (this.isProcess) {
            return;
        }
        this.setButtonsDisabled(true);
        if (callback) {
            let shouldClose;
            try {
                shouldClose = await callback();
            } catch (e) {
                this.props.close();
                throw e;
            }
            if (shouldClose === false) {
                this.setButtonsDisabled(false);
                return;
            }
        }
        this.props.close();
    }
}
