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
        this.store = useService("mail.store");
        const uid = this.env.services?.user?.uid;
        if (uid) {
            this.orm.call(
                'mail.wizard.recipient',
                'get_user',
                [uid]
            );
        }
    },
    async scheduleLogNote() {
        //    ------to schedule lognote -------------
        const model = this.thread.model;
        const id = this.thread.id;
        const message = this.props.composer.textInputContent;
        const attachments = this.props.composer.attachments.map((attachment) => attachment.id);
        const recipient = this.thread.recipients;
        const mentioned_list = [];
        // Ensure body is a string
        const body = this.props.composer.textInputContent || "";

        // Ensure mentions arrays are valid
        const mentionedChannels = this.props.composer.mentionedChannels || [];
        const mentionedPartners = this.props.composer.mentionedPartners || [];

        const validMentions = this.store.getMentionsFromText(body, {
            mentionedChannels: mentionedChannels,
            mentionedPartners: mentionedPartners,
        });
        validMentions.partners.forEach(mentions => {
            mentioned_list.push(mentions.id);
        });
        // RecipientsInput uses thread.suggestedRecipients + thread.additionalRecipients
        // We must do the same to match the UI exactly.
        var followers_list = [];
        const thread = this.props.composer.thread;
        const allRecipients = [
            ...(thread.suggestedRecipients || []),
            ...(thread.additionalRecipients || [])
        ];


        if (allRecipients) {
            allRecipients.forEach(recipient => {
                // Extract partner ID handling multiple structures:
                // 1. Standard Odoo recipient: { partner_id: 123, ... }
                // 2. My custom follower object: { persona: { id: 456, ... } } (from composer_patch.js)
                // 3. Generic/fallback: { id: 789 } (if partner record)
                // 4. Partner wrapper: { partner: { id: ... } } (sometimes seen)

                const partnerId = recipient.partner_id || recipient.persona?.id || recipient.partner?.id || recipient.id;

                // Ensure valid numeric ID and uniqueness
                if (partnerId && typeof partnerId === 'number' && !followers_list.includes(partnerId)) {
                    followers_list.push(partnerId);
                }
            });
        }

        if (this.props.type === "note") {
            const action = {
                type: 'ir.actions.act_window',
                res_model: 'schedule.log',
                domain: [],
                views: [[false, "form"], [false, "list"],],
                name: "Schedule log",
                target: 'new',
                context: {
                    default_body: await prettifyMessageContent(message, validMentions),
                    default_attachment_ids: attachments,
                    default_partner_ids: mentioned_list,
                    default_is_log: 1,
                    default_model: model,
                    default_model_reference: id,
                    default_subtype_xmlid: "mail.mt_note",
                },
            };
            this.env.services.action.doAction(
                action,
                {
                }
            );
            this.clear()
        }
        else {
            const action = {
                type: 'ir.actions.act_window',
                res_model: 'schedule.log',
                domain: [],
                views: [[false, "form"], [false, "list"],],
                name: "Schedule Message",
                target: 'new',
                context: {
                    default_body: message,
                    default_attachment_ids: attachments,
                    default_partner_ids: followers_list,
                    default_is_log: 0,
                    default_model: model,
                    default_model_reference: id,
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
