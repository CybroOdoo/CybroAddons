/** @odoo-module **/
import { Chatter } from "@mail/chatter/web_portal/chatter";
import { patch } from "@web/core/utils/patch";
import { _t } from "@web/core/l10n/translation";

patch(Chatter.prototype, {
    /**
     * @override
     * @param {onClickScheduleMail} ev
     */
    async onClickScheduleMail(ev) {
        console.log('onClickScheduleMail')
         const followers_list = this.state.thread.followers.map(follower => follower.partner.id);
            const action = {
                type: 'ir.actions.act_window',
                res_model: 'mail.compose.message',
                view_mode: 'form',
                views: [[false, 'form']],
                name: _t("Send Mail"),
                target: 'new',
                context: {
                    default_res_model: this.state.thread.model,
                    default_res_ids: [this.state.thread.id],
                    default_partner_ids:followers_list,
                },
            };
            this.env.services.action.doAction(action);
    },
});
