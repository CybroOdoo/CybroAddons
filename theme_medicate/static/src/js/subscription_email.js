/** @odoo-module **/
import { _t } from "@web/core/l10n/translation";
import publicWidget from "@web/legacy/js/public/public_widget";
import { ReCaptcha } from "@google_recaptcha/js/recaptcha";
import { jsonrpc } from "@web/core/network/rpc_service";
import { useService } from "@web/core/utils/hooks";

publicWidget.registry.newsletterSubscription = publicWidget.Widget.extend({
    selector: ".container-newsletter",
    disabledInEditableMode: false,
    events: {
        'click .btn-submit': '_onSubscribeClick',
        'keypress .input-email-submit': '_onEnterKey'
    },

    /**
     * @constructor
     */
    init: function (parent, options) {
        this._super.apply(this, arguments);
        this._recaptcha = new ReCaptcha();
        this.notification = useService("notification");
    },

    /**
     * @override
     */
    willStart: function () {
        return Promise.all([
            this._super.apply(this, arguments),
            this._recaptcha.loadLibs()
        ]);
    },

    /**
     * Handle Enter key press on email input
     * @private
     */
    _onEnterKey: function (event) {
        if (event.which === 13) {
            event.preventDefault();
            this._onSubscribeClick();
        }
    },

    /**
     * Validate email and handle subscription
     * @private
     */
    _onSubscribeClick: async function () {
        const $input = this.$('.input-email-submit');
        const email = $input.val().trim();

        if (!email.match(/.+@.+/)) {
            this._showNotification(_t("Please enter a valid email address."), 'danger');
            $input.addClass('is-invalid');
            return false;
        }

        $input.removeClass('is-invalid');

        try {
            const tokenObj = await this._recaptcha.getToken('website_mass_mailing_subscribe');

            if (tokenObj.error) {
                this._showNotification(tokenObj.error, 'danger');
                return false;
            }

            const result = await jsonrpc('/website_mass_mailing/subscribe', {
                'list_id': 1,
                'value': email,
                'subscription_type': 'email',
                'recaptcha_token_response': tokenObj.token,
            });

            const toastType = result.toast_type || 'danger';

            this._showNotification(result.toast_content, toastType);

            if (toastType === 'success') {
                $input.prop('disabled', true);
                this.$('.btn-submit').addClass('disabled');
            }

        } catch (error) {
            this._showNotification(_t("An unexpected error occurred."), 'danger');
        }
    },

    /**
     * Show notification in UI
     * @private
     */
    _showNotification: function (message, type) {
        if (!this.notificationService) {
            return;
        }

        this.notification.add({
            type: type,
            message: message,
            title: type === 'success' ? _t('Success') : _t('Error'),
            sticky: false,
            timeout: 5000
        });
    }
});

export default publicWidget.registry.newsletterSubscription;
