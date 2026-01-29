/** @odoo-module **/
import { patch } from 'web.utils';
import { Composer } from '@mail/components/composer/composer';
import { _t } from 'web.core';
import { useService } from "@web/core/utils/hooks";


patch(Composer.prototype, 'odoo_advanced_chatter/static/src/js/schedule_mail.js', {
    setup() {
        this._super();
        this.env.services.rpc({
                model: 'mail.wizard.recipient',
                method: 'get_user',
                args: [this.env.session.user_id[0]]
            });
    },
    async _scheduleLogNote(){
    //----To manage schedule note
        const composer = this.composerView.composer
        const postData =  this.composerView._getMessageData()
        const recipient = composer.check
        var followers_list=[]
        $.each(composer.activeThread.followers,(index,follower) => {followers_list.push(follower.partner.id)});
        if (recipient){
            recipient.forEach(item=>{
                const index = followers_list.indexOf(item);
                if (index !== -1) {
                    followers_list.splice(index, 1);
                }
            })
        }

        if (!composer.isLog){
            const action = {
                type: 'ir.actions.act_window',
                res_model:'schedule.log',
                domain: [],
                views: [ [false, "form"],[false, "list"],],
                name: this.env._t("Schedule Message"),
                target: 'new',
                context: {
                    default_body:postData.body,
                    default_attachment_ids:postData.attachment_ids,
                    default_is_log:1,
                    default_partner_ids:followers_list,
                    default_model:composer.thread.model,
                    default_model_reference:composer.thread.id,
                },
            };
            await this.env.bus.trigger('do-action', { action });
        }
        else{
            const action = {
                type: 'ir.actions.act_window',
                res_model:'schedule.log',
                domain: [],
                views: [ [false, "form"],[false, "list"],],
                name: this.env._t("Schedule Log"),
                target: 'new',
                context: {
                    default_body:postData.body,
                    default_attachment_ids:postData.attachment_ids,
                    default_partner_ids:followers_list,
                    default_is_log:0,
                    default_model:composer.thread.model,
                    default_model_reference:composer.thread.id,
                },
            };
            await this.env.bus.trigger('do-action', { action });
        }
        composer._reset();
        this.composerView.delete()
    },
    replyTo() {
    //---To manage recipients in the followers list
        var userId = this.env.session.user_id[0]
            const action = {
            type: "ir.actions.act_window",
            res_model: "mail.wizard.recipient",
            view_mode: "form",
            views: [[false, "form"]],
            name: _t("Reply To"),
            target: "new",
            context: {
                default_partner_id:userId,
            },
        }
        this.env.bus.trigger('do-action', { action })
    }
})
