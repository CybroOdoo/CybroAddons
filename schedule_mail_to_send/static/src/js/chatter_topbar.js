/** @odoo-module **/
import { registerPatch } from '@mail/model/model_core';
import core from 'web.core';
import rpc from 'web.rpc';
registerPatch({
    name: 'Chatter',
    recordMethods: {
    //This function is used to open the mail compose window with corresponding followers as recipient of mail
        async onClickScheduleMail(ev) {
              var followers_list=[]
         $.each(this.thread.followers,(index,follower) => {
         followers_list.push(follower.partner.id)
         });
            const action = {
                type: 'ir.actions.act_window',
                res_model: 'mail.compose.message',
                view_mode: 'form',
                views: [[false, 'form']],
                name: this.env._t("Send Mail"),
                target: 'new',
                context: {
                    default_res_model: this.thread.model,
                    default_res_id: this.thread.id,
                    default_partner_ids:followers_list,
                },
            };
            this.env.services.action.doAction(action);
    },
    },
});
