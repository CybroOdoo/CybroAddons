/** @odoo-module **/

import { registerPatch } from '@mail/model/model_core';
import { patch } from '@web/core/utils/patch';


registerPatch({
    name: 'ComposerView',
    recordMethods: {
        //-------To schedule log note and send message
        scheduleLogNote(event) {
            const composer = this.composer;
            const postData = this._getMessageData();
            const recipient = this.composer.check
            var followers_list=[]
            $.each(composer.thread.followers,(index,follower) => {
            followers_list.push(follower.partner.id)
            });
            if (recipient){
            recipient.forEach(item=>{
                const index = followers_list.indexOf(item);
            if (index !== -1) {
                followers_list.splice(index, 1);
                }
            })
            }
            if (!this.composer.isLog ){
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
            this.env.services.action.doAction(
            action,
        {
        }
        );
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
            this.env.services.action.doAction(
            action,
        {
        }
        );
        }
        },

    },
});
