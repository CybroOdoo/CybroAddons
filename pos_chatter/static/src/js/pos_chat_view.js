/** @odoo-module **/
import ajax from 'web.ajax';
const { xml,onMounted,useState,useExternalListener, useRef } = owl;
export class ChatMsgView extends owl.Component {
    setup() {
        super.setup(...arguments);
        this.flag_scroll = 1
        this.flag = 0
        this.root = useRef("root")
        onMounted(this.render_messages)
        useExternalListener(window, "click", this.ext_close_window, true);
        this.state = owl.useState({
            'name': {},
            'data': {},
            'id': {}
        })
    }
    /** function for the enter key to send messages*/
    keyEnter(event) {
        var self = this
        if (event.key === "Enter") {
            self._onClickMessageSend()
        }
    }
    /** for running the function passing flag values*/
    /** getting old message*/
    render_messages() {
        var self = this
        ajax.jsonRpc('/pos_systray/chat_message', 'call', {
            'data': self.props.channel_id
        }).then(function(result) {
            if (self.flag_scroll == 1) {
                var element = this.root.el.querySelector("#msg_content");
                element.scrollTop = element.scrollHeight;
            }
            var message_list = []
            var messages = result.messages
            $(messages).each(function(message) {
                const htmlString = messages[message].body;
                const parser = new DOMParser();
                const parsedHtml = parser.parseFromString(htmlString, 'text/html');
                const plainText = parsedHtml.documentElement.textContent;
                message_list.push({
                    'body': plainText,
                    'author': messages[message].author,
                    'flag': messages[message].flag
                })
            });
            self.state.data = message_list;
            self.state.name = result.name;
            self.state.id = result.channel_id;
        })
        if (self.flag == 0) {
            setTimeout(this.render_messages.bind(this), 1000);
            self.flag_scroll = 0
        }
    }
    /** for closing the chat window*/
    close_window() {
        this.__owl__.remove()
        this.flag = 1
        this.flag_scroll = 0
    }
    /** for closing the opened chat window */
    ext_close_window(ev) {
        console.log(this.root.el)
        if(this.root.el){
            if (!this.root.el.contains(ev.target)) {
                this.__owl__.remove()
                this.flag = 1
                this.flag_scroll = 0
            }
        }
    }
    /** for sending the message*/
    _onClickMessageSend() {
        var self = this
        var input_value = this.root.el.querySelector("#message_to_send")
        var res_id = this.root.el.querySelector("#button_send").getAttribute("value")
        var element = this.root.el.querySelector("#msg_content");
        element.scrollTop = element.scrollHeight;
        if (input_value.value) {
            var data = {
                'res_id': res_id,
                'msg_body': input_value.value
            }
            ajax.jsonRpc('/pos_chatter/send_message', 'call', {
                'data': data
            }).then(function() {
                input_value.value = ""
                var res_id = self.root.el.querySelector("#button_send").getAttribute("value")
                self.render_messages();
                var element = self.root.el.querySelector("#msg_content");
                element.scrollTop = element.scrollHeight;
            })
        }
    }
}
ChatMsgView.template = xml`
    //template for pos chat view
    <div id="pos_chat_view" style="position:fixed;width:325px;background:#fff;bottom:5px;right:5px;height:500px;border-radius:10px;" t-ref="root">
    <div style="width=100%;background:#875A7B;height:36px;border-top-left-radius: 10px;border-top-right-radius: 10px;">
        <div style="padding: 10px;display:flex;">
            <i style="margin-left:10px;color: white;width:30px;" class="fa fa-lock" />
            <span style="margin-left:5px;color: white;width:225px;" t-esc="state.name" />
            <i style="color: white;width:30px;cursor: pointer;text-align: center;" t-on-click="close_window" class="fa fa-times" />
        </div>
        <div id="msg_content" style="height:400px;background-color: white;overflow-y: scroll;">
            <t t-foreach="state.data" t-as="data" t-key="state.id">
                <t t-if="data['flag'] == 0">
                    <p style="text-align:left;margin-left: 10px;"><small style="color:#9c9a97;" t-esc="data['author']" />
                        <br />
                        <t t-raw="data['body']" />
                    </p>
                </t>
                <t t-else="">
                    <p style="text-align:right;margin-right: 10px;"><small style="color:#9c9a97;"> You </small>
                        <br />
                        <t t-esc="data['body']" />
                    </p>
                </t>
            </t>
        </div>
        <hr />
        <div>
            <input id="message_to_send" type="text" style="border:none;width: 265px;margin-left: 17px;outline:none;height: 25px;" placeholder="Message" t-on-keypress="keyEnter" />
            <i style="margin-left:7px;cursor: pointer;" id="button_send" class="fa fa-paper-plane" t-att-value="state.id" t-on-click="_onClickMessageSend" />
        </div>
    </div>
</div>`
