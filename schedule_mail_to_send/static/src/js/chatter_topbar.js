/** @odoo-module **/

import { ChatterTopbar } from '@mail/components/chatter_topbar/chatter_topbar';
import { patch } from 'web.utils';
patch(ChatterTopbar.prototype, 'mail/static/src/components/chatter_topbar/chatter_topbar.js', {
//This function is used to open the mail compose window with corresponding followers as recipient of mail
    onClickScheduleMail(ev){
         var model = this.chatter.__values.threadModel
         var followers_list=[]
         $.each(this.chatter.thread.followers,(index,follower) => {
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
                    default_res_model: model,
                    default_res_id:this.chatter.thread.id,
                    default_partner_ids:followers_list,
                },
            };
              return this.env.bus.trigger('do-action', {
                action,
                options: {
                    on_close: () => {
                        if (!this.componentChatterTopbar) {
                            return;
                        }
                        this.componentChatterTopbar.trigger('reload', { keepChanges: true });
                    },
                },
            });
        }
});
