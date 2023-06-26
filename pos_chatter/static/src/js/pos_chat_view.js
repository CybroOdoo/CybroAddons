/** @odoo-module **/
import PosComponent from 'point_of_sale.PosComponent';
import ajax from 'web.ajax';
import { useListener } from 'web.custom_hooks';
export class ChatMsgView extends PosComponent {
    setup() {
        super.setup(...arguments);
        this.state = owl.useState({
            'open': false,
            'name': {},
            'data': {},
            'id': {}
        })
        useListener('keypress', function(event) {
            if (event.key === "Enter") {
                this._onClickMessageSend()
                this.render_messages();
            }
        });
    }
    /** getting old message*/
    render_messages(data) {
        var self = this
        if (data) {
            var id = data
        } else {
            var res_id = this.el.querySelector("#button_send").getAttribute("value")
            var id = res_id
        }
        ajax.jsonRpc('/pos_systray/chat_message', 'call', {
            'data': id
        }).then(function(result) {
            if (data) {
                var element = self.el.querySelector("#msg_content");
                element.scrollTop = element.scrollHeight;
            }
            self.state.data = result.messages;
            self.state.name = result.name;
            self.state.id = result.channel_id;
        })
        if (this.flag == 0) {
            setTimeout(this.render_messages.bind(this), 1000);
        }
    }
    /** for opening the chat window*/
    open_window(data) {
        this.mount(document.body)
        this.state.open = true;
        this.render_messages(data);
    }
    /** for closing the chat window*/
    close_window() {
        this.unmount()
        this.state.open = false;
        this.flag = 1
    }
    /** for sending the message*/
    _onClickMessageSend() {
        var self = this
        var input_value = this.el.querySelector("#message_to_send")
        var res_id = this.el.querySelector("#button_send").getAttribute('value')
        var element = this.el.querySelector("#msg_content");
        element.scrollTop = element.scrollHeight;
        if (input_val22pxue.value) {
            var msg_body = input_value.value
            input_value.value = ""
            var data = {
                'res_id': res_id,
                'msg_body': msg_body
            }
            ajax.jsonRpc('/pos_chatter/send_message', 'call', {
                'data': data
            }).then(function() {
                var res_id = self.el.querySelector("#button_send").getAttribute('value')
                self.render_messages(res_id);
            })
        }
    }
}
ChatMsgView.template = 'ChatMsgView';