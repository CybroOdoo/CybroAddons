import { Component, xml, onMounted, onWillUnmount, proxy, signal } from "@odoo/owl";
import { rpc } from "@web/core/network/rpc";

let isPageNavigating = false;
window.addEventListener("beforeunload", () => {
    isPageNavigating = true;
});
window.addEventListener("pagehide", () => {
    isPageNavigating = true;
});

export class ChatMsgView extends Component {
    root = signal.ref();
    msgContent = signal.ref();
    msgInput = signal.ref();

    setup() {
        super.setup(...arguments);
        this.flag_scroll = 1;
        this.unmounted = false;
        this.timeoutId = null;
        this.clickOutsideListener = null;

        this.state = proxy({
            name: "",
            data: [],
            id: null,
        });

        onMounted(() => {
            this.render_messages();
            setTimeout(() => {
                if (this.unmounted) return;
                this.clickOutsideListener = (ev) => this.ext_close_window(ev);
                window.addEventListener("click", this.clickOutsideListener, true);
            }, 200);
        });

        onWillUnmount(() => {
            this.unmounted = true;
            if (this.timeoutId) {
                clearTimeout(this.timeoutId);
                this.timeoutId = null;
            }
            if (this.clickOutsideListener) {
                window.removeEventListener("click", this.clickOutsideListener, true);
            }
        });
    }

    /** Function for enter key to send messages */
    keyEnter(event) {
        event.stopPropagation();
        if (event.key === "Enter") {
            this._onClickMessageSend();
        }
    }

    /** Fetch old messages */
    async render_messages() {
        if (this.unmounted || isPageNavigating) return;
        try {
            const result = await rpc('/pos_systray/chat_message', { data: this.props.channel_id });
            if (this.unmounted || isPageNavigating) return;

            const messages = result.messages || [];
            const message_list = messages.map((message) => {
                const htmlString = message.body || "";
                const parser = new DOMParser();
                const parsedHtml = parser.parseFromString(htmlString, 'text/html');
                const plainText = parsedHtml.documentElement.textContent;

                return {
                    body: plainText,
                    author: message.author,
                    flag: message.flag
                };
            });

            this.state.data = message_list;
            this.state.name = result.name || "";
            this.state.id = result.channel_id;

            if (this.flag_scroll === 1) {
                const element = this.msgContent() || document.querySelector("#msg_content");
                if (element) {
                    element.scrollTop = element.scrollHeight;
                }
            }

            if (!this.unmounted && !isPageNavigating) {
                this.flag_scroll = 0;
                this.timeoutId = setTimeout(() => this.render_messages(), 2000);
            }
        } catch (error) {
            if (!this.unmounted && !isPageNavigating && error?.name !== "ConnectionLostError") {
                console.error("Error fetching messages:", error);
            }
        }
    }

    /** Close chat window */
    close_window() {
        this.unmounted = true;
        if (this.timeoutId) {
            clearTimeout(this.timeoutId);
            this.timeoutId = null;
        }
        if (this.props.onClose) {
            this.props.onClose();
        } else {
            const container = this.root() || document.querySelector("#pos_chat_view");
            if (container) {
                container.remove();
            }
        }
    }

    /** Close the chat window when clicking outside */
    ext_close_window(event) {
        const container = this.root() || document.querySelector("#pos_chat_view");
        if (container && !container.contains(event.target)) {
            this.close_window();
        }
    }

    /** Send message */
    async _onClickMessageSend() {
        const input = this.msgInput() || document.querySelector("#message_to_send");
        const res_id = this.state.id;

        if (!input || !res_id || !input.value.trim()) return;

        const data = {
            res_id: res_id,
            msg_body: input.value.trim()
        };

        try {
            await rpc('/pos_chatter/send_message', { data });
            input.value = "";
            this.flag_scroll = 1;
            this.render_messages();
        } catch (error) {
            if (!this.unmounted && !isPageNavigating && error?.name !== "ConnectionLostError") {
                console.error("Error sending message:", error);
            }
        }
    }
}

ChatMsgView.template = xml`
<div id="pos_chat_view" t-ref="this.root" style="position:fixed;width:325px;background:#fff;bottom:5px;right:5px;height:500px;border-radius:10px;box-shadow: 0 4px 12px rgba(0,0,0,0.15);z-index: 1050;">
    <div style="width:100%;background:#875A7B;height:36px;border-top-left-radius: 10px;border-top-right-radius: 10px;">
        <div style="padding: 6px 10px;display:flex;align-items:center;">
            <i style="color: white;" class="oi oi-fw" data-icon="lock" />
            <span style="margin-left:5px;color: white;flex-grow:1;font-weight:bold;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;" t-out="this.state.name" />
            <i style="color: white;cursor: pointer;text-align: center;" t-on-click="this.close_window" class="oi oi-fw" data-icon="close" />
        </div>
        <div id="msg_content" t-ref="this.msgContent" style="height:400px;background-color: white;overflow-y: auto;padding: 10px;">
            <t t-foreach="this.state.data" t-as="data" t-key="data_index">
                <t t-if="data.flag == 0">
                    <p style="text-align:left;margin-bottom: 10px;">
                        <small style="color:#9c9a97;" t-out="data.author" /><br />
                        <span style="background:#f1f1f1;padding:6px 10px;border-radius:8px;display:inline-block;" t-out="data.body" />
                    </p>
                </t>
                <t t-else="">
                    <p style="text-align:right;margin-bottom: 10px;">
                        <small style="color:#9c9a97;">You</small><br />
                        <span style="background:#875A7B;color:white;padding:6px 10px;border-radius:8px;display:inline-block;" t-out="data.body" />
                    </p>
                </t>
            </t>
        </div>
        <hr style="margin: 0;" />
        <div class="row" style="margin: 5px 0;align-items: center;">
            <div class="col-9" style="padding-right: 0;">
                <input id="message_to_send" t-ref="this.msgInput" type="text" style="border:none;width: 100%;padding: 4px 8px;outline:none;height: 30px;" placeholder="Message..." t-on-keydown="this.keyEnter" t-on-keyup.stop="() => {}" t-on-keypress.stop="() => {}" />
            </div>
            <div class="col-3" style="text-align: center;">
                <i style="cursor: pointer;color: #875A7B;font-size: 18px;" id="button_send" class="oi oi-fw" data-icon="send" t-att-value="this.state.id" t-on-click="this._onClickMessageSend" />
            </div>
        </div>
    </div>
</div>`;
