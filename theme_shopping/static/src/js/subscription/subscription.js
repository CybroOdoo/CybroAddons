/** @odoo-module **/
import { _t } from "@web/core/l10n/translation";
import { rpc } from "@web/core/network/rpc";
import publicWidget from "@web/legacy/js/public/public_widget";
import {ReCaptcha} from "@google_recaptcha/js/recaptcha";
publicWidget.registry.subscription = publicWidget.Widget.extend({
    selector: ".subscription_template",
    disabledInEditableMode: false,
    read_events: {
        'click .st-newsletter_subscribe--btn': '_onSubscribeClick',
    },
    /**
     * @constructor
     */
    init: function () {
        this._super(...arguments);
        this._recaptcha = new ReCaptcha();
        this.rpc = rpc;
        this.notification = this.bindService("notification");
    },
    /**
     * @override
     */
    willStart: function () {
        this._recaptcha.loadLibs();
        return this._super(...arguments);
    },
    /**
     * @override
     */
    _getListId: function () {
        return this.$el.closest('[data-snippet=s_newsletter_block').data('list-id') || this.$el.data('list-id');
    },
    _onSubscribeClick: async function () {
        var self = this;
        const inputName = this.$('input').attr('name');
        const $input = this.$(".st-newsletter_input:visible, .js_subscribe_email:visible"); // js_subscribe_email is kept by compatibility (it was the old name of js_subscribe_value)
        if (inputName === 'email' && $input.length && !$input.val().match(/.+@.+/)) {
            this.$el.addClass('o_has_error').find('.form-control').addClass('is-invalid');
            return false;
        }
        this.$el.removeClass('o_has_error').find('.form-control').removeClass('is-invalid');
        const tokenObj = await this._recaptcha.getToken('website_mass_mailing_subscribe');
        if (tokenObj.error) {
            self.notification.add(tokenObj.error, {
                type: 'danger',
                title: _t("Error"),
                sticky: true,
            });
            return false;
        }
        this.rpc('/website_mass_mailing/subscribe', {
            'list_id': 1,
            'value': $input.length ? $input.val() : false,
            'subscription_type': inputName,
            recaptcha_token_response: tokenObj.token,
        }).then(function (result) {
            let toastType = result.toast_type;
            if (toastType === 'success') {
                self.$(".js_subscribe_btn").addClass('d-none');
                self.$(".js_subscribed_btn").removeClass('d-none');
                self.$('input.js_subscribe_value, input.js_subscribe_email').prop('disabled', !!result); // js_subscribe_email is kept by compatibility (it was the old name of js_subscribe_value)
                const $popup = self.$el.closest('.o_newsletter_modal');
                if ($popup.length) {
                    $popup.modal('hide');
                }
            }
            self.notification.add(result.toast_content, {
                type: toastType,
                title: toastType === 'success' ? _t('Success') : _t('Error'),
                sticky: true,
            });
        });
    },
});
