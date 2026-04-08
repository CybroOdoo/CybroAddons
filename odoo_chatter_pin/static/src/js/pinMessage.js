/** @odoo-module **/
/**
 * Registers a custom message action for pinning/unpinning chat messages.
 * The action appears only for logged-in users and toggles the pinned status
 * when selected.
 */
import { _t } from "@web/core/l10n/translation";
import { registerMessageAction } from "@mail/core/common/message_actions";

registerMessageAction("pin_message", {
    condition: ({ store, thread }) => store.self_partner,
    icon: "fa fa-thumb-tack",
    name: ({ message }) => (message.pinned_at ? _t("Unpin") : _t("Pin")),
    sequence: 15,
    onSelected: ({ message }) => message.onClickPin(),
});
