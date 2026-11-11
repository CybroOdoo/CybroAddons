/** @odoo-module */
import { Component, useProps, t } from "@odoo/owl";
import { _t } from "@web/core/l10n/translation";
import { Dialog } from "@web/core/dialog/dialog";

/**
 * CustomMessageInfoPopup component for displaying custom messages as an
 * informational popup.
 */
export class CustomMessageInfoPopup extends Component {
    static template = "pos_custom_message.CustomMessageInfoPopup";
    static components = { Dialog };
    props = useProps({
        title: t.string().optional(""),
        body: t.string().optional(""),
        confirmText: t.string().optional(() => _t("Ok")),
        close: t.function(),
    });

    cancel() {
        this.props.close();
    }
}
