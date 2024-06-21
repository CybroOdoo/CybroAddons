/** @odoo-module **/
import { Composer } from "@mail/core/common/composer";
import { patch } from "@web/core/utils/patch";
import { prettifyMessageContent, escapeAndCompactTextContent } from "@mail/utils/common/format";
import { useRef } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";
patch(Composer.prototype, {
    setup() {
        super.setup();
        this.orm = useService("orm");
        this.orm.call(
            'mail.wizard.recipient',
            'get_user',
            [this.env.model.user.userId]
        )
    },
    async scheduleLogNote(){
        //    ------to schedule lognote -------------
        const model = this.thread.model;
        const id = this.thread.id;
        const message = this.props.composer.textInputContent;
        const attachments = this.props.composer.attachments.map((attachment) => attachment.id);
        const recipient = this.threadService.check;
        const mentioned_list = [];
        const validMentions = this.store.user
            ? this.messageService.getMentionsFromText(message, {
                  mentionedChannels: this.props.composer.mentionedChannels,
                  mentionedPartners: this.props.composer.mentionedPartners,
            })
            : undefined;
        $.each(validMentions.partners,(index,mentions) => {
            mentioned_list.push(mentions.id)
        });
        var followers_list=[]
        $.each( this.props.composer.thread.followers,(index,follower) => {
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
        if (this.props.type === "note" ){
            const action = {
               type: 'ir.actions.act_window',
                res_model:'schedule.log',
                domain: [],
                views: [ [false, "form"],[false, "list"],],
                name: "Schedule log",
                target: 'new',
                context: {
                    default_body: await prettifyMessageContent(message, validMentions),
                    default_attachment_ids:attachments ,
                    default_partner_ids:mentioned_list,
                    default_is_log:1,
                    default_model:model,
                    default_model_reference:id,
                    default_subtype_xmlid:  "mail.mt_note",
                },
            };
            this.env.services.action.doAction(
                action,
        {
        }
        );
        this.clear()
        }
        else{
            const action = {
               type: 'ir.actions.act_window',
                res_model:'schedule.log',
                domain: [],
                views: [ [false, "form"],[false, "list"],],
                name: "Schedule Message",
                target: 'new',
                context: {
                    default_body:message,
                    default_attachment_ids:attachments ,
                    default_partner_ids:followers_list,
                    default_is_log:0,
                    default_model:model,
                    default_model_reference:id,
                },
            };
            this.env.services.action.doAction(
            action,
        {
        }
        );
        this.clear()
        }
    }
})
