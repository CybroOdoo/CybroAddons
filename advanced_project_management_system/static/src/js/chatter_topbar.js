/** @odoo-module **/
import { registerModel, registerPatch } from '@mail/model/model_core';
import { one, attr, many } from '@mail/model/model_field';
// Register the 'Comment' model
registerModel({
    name: 'Comment',
    fields: {
        text: attr(),
        chatter: one('Chatter',{
            inverse: 'comments'
        }),
        author: one('Partner'),
        isDeleted: attr({ default: false }),
    },
});
// Register a patch for the 'Chatter' model
registerPatch({
    name: 'Chatter',
    fields: {
        partner: one('Partner'),
        comments: one('Comment', {
            inverse: 'chatter',
        }),
    },
    recordMethods: {
        async onClickComment() {
                this.showLogNote();
                this.composerView.composer.update({ placeholder: 'Comments...' })
        },
        onClickSendMessage(ev) {
            this._super(ev);
        }
     }
    });
    // Register a patch for the 'MessageView' model
registerPatch({
    name: 'MessageView',
    fields: {
        notificationIconClassName: {
            compute() {
                if (this.message && this.message.message_type === 'comment') {
                    return 'fa fa-comment';
                }
                return this._super();
            },
        },
            },
            });
