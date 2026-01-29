/** @odoo-module **/

import * as mailUtils from '@mail/js/utils';

import { useService } from "@web/core/utils/hooks";
const { Component } = owl;
import { ThreadPreview } from '@mail/components/thread_preview/thread_preview'
import { patch } from 'web.utils';
import emojis from '@mail/js/emojis';
patch(ThreadPreview.prototype, 'chat_quick_reply', {

     setup() {
            this._super();
            this.emojis = emojis
            this.rpc = useService("rpc");

        },
    _onClickQuickReply(ev) {
            this.el.querySelector('.quick_reply').style.display = 'flex';
        },
    composeMessage(ev){
    },
    onClickEmoji(ev){
            $('#EmojiContainer')[0].classList.toggle('d-none')
            var div_display = this.el.querySelector('#EmojiContainer').style
                div_display.display = "block";
        },
    emojiSelect(emoji) {
        const currentValue = $('#reply_message').val();
        const updatedValue = currentValue + emoji.unicode;
        this.inputValue = updatedValue
        $('#reply_message').val(updatedValue);
    },
    get_thread() {
     return this.messaging && this.messaging.models['mail.thread'].get(this.props.threadLocalId);
    },

    async onClickSendReply(ev) {
            const body = $('#reply_message').val()
            this.rpc({route:'/message/post', params:{
                'post_data': {'body': body},
                'thread_id': this.get_thread().id,
                'subtype_xmlid': 'mail.mt_comment',
                'thread_model': 'mail.channel',
            }}).then(() =>{
                this.el.querySelector('.quick_reply').style.display = 'none';
                this.el.querySelector('#EmojiContainer').style.display = 'none';
                this.el.querySelector('#reply_message').value = '';
            })

        },
})
