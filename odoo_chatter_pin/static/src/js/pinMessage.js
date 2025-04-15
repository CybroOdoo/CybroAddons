/* @odoo-module */
import { _t } from "@web/core/l10n/translation";
import { messageActionsRegistry } from "@mail/core/common/message_actions";

messageActionsRegistry.add("pins", {
    condition: (component) =>
        component.canAddReaction,
    icon: "fa-thumb-tack",
    title: _t("Pin"),
    onClick: (component) => component.onClickPin(),
    sequence: 15,
});
