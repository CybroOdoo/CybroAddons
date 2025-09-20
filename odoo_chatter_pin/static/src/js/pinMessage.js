/** @odoo-module **/
import { _t } from "@web/core/l10n/translation";
import { messageActionsRegistry } from "@mail/core/common/message_actions";

messageActionsRegistry.add("pin_message", {
    condition: (component) => component && component.props.message,
    icon: "fa fa-thumb-tack",
    title: _t("Pin"),
    sequence: 15,
    onClick: (component) => {
        component.onClickPin?.();
    },
});