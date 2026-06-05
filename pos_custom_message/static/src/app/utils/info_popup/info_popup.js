import { Component } from "@odoo/owl";
import { Dialog } from "@web/core/dialog/dialog";
import { _t } from "@web/core/l10n/translation";

export class InfoPopup extends Component {
    static template = "pos_custom_message.InfoPopup";
    static components = { Dialog };
        static props = {
         title: '',
         body: '',
         confirmLabel: { type: String, optional: true },
         confirmClass: { type: String, optional: true },
         confirm: { type: Function, optional: true },
    };
    static defaultProps = {
        confirmLabel: _t("Ok"),
        confirmClass: "btn-primary",
    };
    async _confirm() {
        this.props.close();
    }
}

