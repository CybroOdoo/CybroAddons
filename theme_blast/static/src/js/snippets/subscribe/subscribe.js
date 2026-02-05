/** @odoo-module **/

import { _t } from "@web/core/l10n/translation";
import publicWidget from "@web/legacy/js/public/public_widget";
import { rpc } from "@web/core/network/rpc";
import { ReCaptcha } from "@google_recaptcha/js/recaptcha";

/**
 * BlastSubscribe
 * Handles newsletter subscription with UI reset on load
 */
publicWidget.registry.BlastSubscribe = publicWidget.Widget.extend({
    selector: ".js_subscribe",
    disabledInEditableMode: false,

    events: {
        "click .js_subscribe_btn": "_onSubscribeClick",
    },

    init() {
        this._super(...arguments);
        this._recaptcha = new ReCaptcha();
        this.rpc = rpc;
        this.notification = this.bindService("notification");
    },

    async willStart() {
        await this._recaptcha.loadLibs();
    },

    /**
     * ✅ IMPORTANT: Reset UI on page load
     */
    start() {
        this.$(".js_subscribed_wrap").addClass("d-none");
        this.$(".js_subscribe_wrap").removeClass("d-none");
        return this._super(...arguments);
    },

    _getListId() {
        return (
            this.$el.data("list-id") ||
            this.$el.closest("[data-list-id]").data("list-id") ||
            0
        );
    },

    async _onSubscribeClick(ev) {
        ev.preventDefault();

        const $input = this.$(".js_subscribe_value");
        const value = $input.val()?.trim();

        if (!value || !/.+@.+/.test(value)) {
            $input.addClass("is-invalid");
            return;
        }

        $input.removeClass("is-invalid");

        try {
            const tokenObj = await this._recaptcha.getToken(
                "website_mass_mailing_subscribe"
            );

            if (tokenObj.error) {
                this.notification.add(tokenObj.error, {
                    type: "danger",
                    sticky: true,
                });
                return;
            }

            const result = await this.rpc(
                "/website_mass_mailing/subscribe",
                {
                    list_id: this._getListId(),
                    value: value,
                    subscription_type: "email",
                    recaptcha_token_response: tokenObj.token,
                }
            );

            if (result.toast_type === "success") {
                this.$(".js_subscribe_wrap").addClass("d-none");
                this.$(".js_subscribed_wrap").removeClass("d-none");
            }

            this.notification.add(
                result.toast_content || _t("Subscription processed"),
                {
                    type: result.toast_type || "info",
                    sticky: true,
                }
            );
        } catch (err) {
            console.error(err);
            this.notification.add(_t("Something went wrong"), {
                type: "danger",
            });
        }
    },
});
