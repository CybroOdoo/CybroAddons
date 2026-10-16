import { Interaction } from '@web/public/interaction';
import { registry } from '@web/core/registry';
import { rpc } from '@web/core/network/rpc';
import { _t } from '@web/core/l10n/translation';
import { ReCaptcha } from '@google_recaptcha/js/recaptcha';

class Subscription extends Interaction {
    static selector = '.subscription_template';
    dynamicContent = {
        '.st-newsletter_subscribe--btn': { 't-on-click.prevent': this.subscribe },
    };
    setup() {
        this.recaptcha = new ReCaptcha();
    }
    async willStart() {
        await this.recaptcha.loadLibs();
    }
    async subscribe() {
        if (this.submitting) return;
        const input = this.el.querySelector('input[name="email"]');
        if (!input.value || !input.reportValidity()) return;
        const listId = Number(this.el.querySelector('[data-list-id]')?.dataset.listId);
        if (!listId) {
            this.services.notification.add(_t('Please select a mailing list in the website editor.'), { type: 'warning' });
            return;
        }
        this.submitting = true;
        try {
            const token = await this.waitFor(this.recaptcha.getToken('website_mass_mailing_subscribe'));
            if (token.error) {
                this.services.notification.add(token.error, { type: 'danger' });
                return;
            }
            const result = await this.waitFor(rpc('/website_mass_mailing/subscribe', {
                list_id: listId,
                value: input.value,
                subscription_type: 'email',
                recaptcha_token_response: token.token,
            }));
            if (result.toast_type === 'success') {
                input.disabled = true;
                this.el.querySelector('.js_subscribe_btn').classList.add('d-none');
                this.el.querySelector('.js_subscribed_btn').classList.remove('d-none');
            }
            this.services.notification.add(result.toast_content, { type: result.toast_type });
        } finally {
            this.submitting = false;
        }
    }
}
registry.category('public.interactions').add('theme_shopping.subscription', Subscription);
