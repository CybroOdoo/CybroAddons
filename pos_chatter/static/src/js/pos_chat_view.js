/** @odoo-module **/
import { rpc } from "@web/core/network/rpc";
const { xml, onMounted, useState, useExternalListener, useRef } = owl;

export class ChatMsgView extends owl.Component {
    setup() {
        super.setup(...arguments);
        this.flag_scroll = 1;
        this.flag = 0;
        this.root = useRef("root");
        onMounted(this.render_messages);
        useExternalListener(window, "click", this.ext_close_window, true);
        this.state = useState({
            name: "",
            data: [],
            id: null
        });
    }

    /** Function for enter key to send messages */
    keyEnter(event) {
        if (event.key === "Enter") {
            this._onClickMessageSend();
        }
    }

    /** Fetch old messages */
    async render_messages() {
        try {
            const result = await rpc('/pos_systray/chat_message', { data: this.props.channel_id });

            if (!this.root.el) return;

            let message_list = [];
            const messages = result.messages || [];

            messages.forEach((message) => {
                const htmlString = message.body;
                const parser = new DOMParser();
                const parsedHtml = parser.parseFromString(htmlString, 'text/html');
                const plainText = parsedHtml.documentElement.textContent;

                message_list.push({
                    body: plainText,
                    author: message.author,
                    flag: message.flag
                });
            });

            this.state.data = message_list;
            this.state.name = result.name;
            this.state.id = result.channel_id;

            if (this.flag_scroll === 1) {
                const element = this.root.el.querySelector("#msg_content");
                if (element) element.scrollTop = element.scrollHeight;
            }

            if (this.flag === 0) {
                setTimeout(() => this.render_messages(), 1000);
                this.flag_scroll = 0;
            }
        } catch (error) {
            console.error("Error fetching messages:", error);
        }
    }

    /** Close chat window */
    close_window() {
        this.__owl__.remove();
        this.flag = 1;
        this.flag_scroll = 0;
    }

    /** Close the chat window when clicking outside */
    ext_close_window(event) {
        if (this.root.el && !this.root.el.contains(event.target)) {
            this.__owl__.remove();
            this.flag = 1;
            this.flag_scroll = 0;
        }
    }

    /** Send message */
    async _onClickMessageSend() {
        if (!this.root.el) return;

        const input = this.root.el.querySelector("#message_to_send");
        const res_id = this.root.el.querySelector("#button_send")?.getAttribute("value");

        if (!input || !res_id || !input.value.trim()) return;

        const data = {
            res_id: res_id,
            msg_body: input.value.trim()
        };

        try {
            await rpc('/pos_chatter/send_message', { data });
            input.value = "";
            this.render_messages();
        } catch (error) {
            console.error("Error sending message:", error);
        }
    }
}

ChatMsgView.template = xml`
<div id="pos_chat_view" style="position:fixed;width:325px;background:#fff;bottom:5px;right:5px;height:500px;border-radius:10px;" t-ref="root">
    <div style="width=100%;background:#875A7B;height:36px;border-top-left-radius: 10px;border-top-right-radius: 10px;">
        <div style="padding: 10px;display:flex;">
            <i style="margin-left:10px;color: white;width:30px;" class="fa fa-lock" />
            <span style="margin-left:5px;color: white;width:225px;" t-esc="state.name" />
            <i style="color: white;width:30px;cursor: pointer;text-align: center;" t-on-click="close_window" class="fa fa-times" />
        </div>
        <div id="msg_content" style="height:400px;background-color: white;overflow-y: scroll;">
            <t t-foreach="state.data" t-as="data" t-key="state.id">
                <t t-if="data.flag == 0">
                    <p style="text-align:left;margin-left: 10px;">
                        <small style="color:#9c9a97;" t-esc="data.author" /><br />
                        <t t-raw="data.body" />
                    </p>
                </t>
                <t t-else="">
                    <p style="text-align:right;margin-right: 10px;">
                        <small style="color:#9c9a97;">You</small><br />
                        <t t-esc="data.body" />
                    </p>
                </t>
            </t>
        </div>
        <hr />
        <div class="row">
            <div class="col-9">
                <input id="message_to_send" type="text" style="border:none;width: 265px;margin-left: 17px;outline:none;height: 25px;" placeholder="Message" t-on-keypress="keyEnter" />
            </div>
            <div class="col-3">
                <i style="margin-left:7px;cursor: pointer;" id="button_send" class="fa fa-paper-plane" t-att-value="state.id" t-on-click="_onClickMessageSend" />
            </div>
        </div>
    </div>
</div>`;
