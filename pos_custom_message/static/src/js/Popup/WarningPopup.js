/** @odoo-module */
import { Component } from "@odoo/owl";
import { _t } from "@web/core/l10n/translation";
import { Dialog } from "@web/core/dialog/dialog";

/**
 * CustomMessageWarnPopup component for displaying custom messages as a warning
 * popup.
 */
export class CustomMessageWarnPopup extends Component {
    static template = "pos_custom_message.CustomMessageWarnPopup";
    static components = { Dialog };
    static props = {
        title: { type: String, optional: true },
        body: { type: String, optional: true },
        confirmText: { type: String, optional: true },
        close: Function,
    };
    static defaultProps = {
        confirmText: _t("Ok"),
        title: "",
        body: "",
    };

    cancel() {
        this.props.close();
    }
}
