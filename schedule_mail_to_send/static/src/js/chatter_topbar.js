/** @odoo-module **/
import { Chatter } from "@mail/core/web/chatter";
import { patch } from "@web/core/utils/patch";
import { _t } from "@web/core/l10n/translation";

patch(Chatter.prototype, {
    /**
     * @override
     * @param {onClickScheduleMail} ev
     */
    async onClickScheduleMail(ev) {
         var followers_list=[]
         $.each(this.state.thread.followers,(index,follower) => {
         followers_list.push(follower.partner.id)
         });
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
