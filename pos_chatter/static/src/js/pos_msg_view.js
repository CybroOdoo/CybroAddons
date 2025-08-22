/** @odoo-module **/
import { rpc } from "@web/core/network/rpc";
const { mount, xml, onMounted, useState, useRef } = owl;
import { ChatMsgView } from "./pos_chat_view";
import { useService } from "@web/core/utils/hooks";


export class PosMsgView extends owl.Component {
    setup() {
        super.setup();
        this.root = useRef("root");
        onMounted(this.render_msg_view);
        this.MsgWindow = new ChatMsgView();
        this.state = useState({
            data: [],
            counts: {
                all: 0,
                chat: 0,
                channels: 0
            }
        });
    }

    /** Fetch all chat messages */
    render_msg_view() {
        rpc("/pos_systray/message_data").then((data) => {
            const message_list = data.map((message) => {
                const parser = new DOMParser();
                const parsedHtml = parser.parseFromString(message.message_body, "text/html");
                let plainText = parsedHtml.documentElement.textContent;

                // Format SMS failure messages
                if (message.type === 'sms_failure') {
                    plainText = `SMS Failure: Contact\nAn error occurred when sending an SMS\nAug 18`;
                }

                return {
                    id: message.id,
                    type: message.type,
                    name: message.name,
                    message_body: plainText,
                    count: message.count || 0,
                };
            });

            // Calculate counts for each category
            const counts = {
                chat: message_list.filter(m => m.type === 'chat').reduce((sum, msg) => sum + msg.count, 0),
                all: message_list.filter(m => m.type === 'channel').reduce((sum, msg) => sum + msg.count, 0),
                channels : message_list.reduce((sum, msg) => sum + msg.count, 0),

            };

            this.state.data = message_list;
            this.state.counts = counts;
        });
    }

    /** Toggle visibility between All, Chat, and Channels */
    toggleView(activeButtonId, activeSectionId) {
        ["all_message", "all_chat", "all_channels"].forEach((id) => {
            this.root.el.querySelector(`#${id}`).style.display = id === activeSectionId ? "block" : "none";
        });

        ["all_message_button", "all_chat_button", "all_channels_button"].forEach((id) => {
            this.root.el.querySelector(`#${id}`).style.color = id === activeButtonId ? "#000" : "#9c9a97";
        });
    }

    _onClickAllMessage() {
        this.toggleView("all_message_button", "all_message");
    }

    _onClickAllChannels() {
        this.toggleView("all_channels_button", "all_channels");
    }

    _onClickAllChat() {
        this.toggleView("all_chat_button", "all_chat");
    }

    /** Open chat view */
    async _onClickToMessage(ev) {
        const channel_id = ev.currentTarget.getAttribute("value");
        if (!channel_id || isNaN(parseInt(channel_id))) {
            console.error("Invalid channel_id:", channel_id);
            alert("Cannot open chat: Invalid message ID");
            return;
        }
        console.log("Channel ID:", channel_id);

        try {
            const result = await rpc("/web/dataset/call_kw/mail.message/compute_read_message", {
                model: "mail.message",
                method: "compute_read_message",
                args: [channel_id],
                kwargs:{}
            });

            this.__owl__.remove();
            this.schedule_dropdown = mount(ChatMsgView, document.body, { props: { channel_id } });
        } catch (error) {
            console.error("RPC Error Details:", {
                message: error.message,
                data: error.data,
                type: error.type,
                stack: error.stack
            });
            alert("Failed to load chat. Please try again.");
        }
    }
}

PosMsgView.template = xml`
    <div class="pos_systray_template" t-ref="root"
        style="height:auto;width:350px;background-color:#f3f3f3;position:fixed;right:5px;top:49px;padding:10px;margin: 7px 14px;">

        <div style="display:flex;height: 27px;position:relative;">
            <div style="display:flex;">
                <p style="margin-left:10px;cursor: pointer;" id="all_message_button"
                   t-on-click="_onClickAllMessage">All</p>
                <p style="margin-left:10px;cursor: pointer;color:#9c9a97;" id="all_chat_button"
                   t-on-click="_onClickAllChat">Chat</p>
                <p style="margin-left:10px;cursor: pointer;color:#9c9a97;" id="all_channels_button"
                   t-on-click="_onClickAllChannels">Channels</p>
            </div>

            <!-- Count badges with exact positioning from image -->
            <span t-if="state.counts.all > 0"
                  style="position:absolute;right:220px;top:-18px;background:#2196F3;color:white;border-radius:50%;
                  width:18px;height:18px;font-size:10px;text-align:center;line-height:18px;"
                  t-esc="state.counts.all"/>

            <span t-if="state.counts.chat > 0"
                  style="position:absolute;right:267px;top:-19px;background:#04AA6D;color:white;border-radius:50%;
                  width:18px;height:18px;font-size:10px;text-align:center;line-height:18px;"
                  t-esc="state.counts.chat"/>

            <span t-if="state.counts.channels > 0"
                  style="position:absolute;right:302px;top:-19px;background:#ffeb3b;color:black;border-radius:50%;
                  width:18px;height:18px;font-size:10px;text-align:center;line-height:18px;"
                  t-esc="state.counts.channels"/>
        </div>

        <hr/>

        <!-- All Messages -->
        <div id="all_message">
            <t t-foreach="state.data" t-as="data" t-key="data.id">
                <div style="background-color: #e7f3fe;border-left: 6px solid #2196F3;
                margin-bottom: 15px;padding: 4px 12px;display:flex;cursor:pointer;position:relative;" t-att-value="data.id"
                    t-on-click="_onClickToMessage">

                    <div style="width:30px">
                        <t t-if="data.type == 'channel'">
                            <i style="margin:40%" class="fa fa-users"/>
                        </t>
                        <t t-elif="data.type == 'sms_failure'">
                            <i style="margin:40%" class="fa fa-exclamation-triangle"/>
                        </t>
                        <t t-else="">
                            <i style="margin:40%" class="fa fa-user"/>
                        </t>
                    </div>

                    <div style="margin-left: 20px;width: 250px">
                        <div style="display:flex;justify-content:space-between;">
                            <span t-esc="data.name"/>
                            <t t-if="data.count > 0">
                                <span style="background-color:#2196F3;color:white;border-radius:50%;
                                      width:18px;height:18px;font-size:10px;text-align:center;
                                      line-height:18px;" t-esc="data.count"/>
                            </t>
                        </div>
                        <small style="color:#9c9a97; white-space: pre-line;" t-raw="data.message_body"/>
                    </div>
                </div>
            </t>
        </div>

        <!-- Chat Messages -->
        <div id="all_chat" style="display:none">
            <t t-foreach="state.data" t-as="data" t-key="data.id">
                <t t-if="data.type == 'chat'">
                    <div style="background-color: #ddffdd;border-left: 6px solid #04AA6D;
                    margin-bottom: 15px;padding: 4px 12px;display:flex;cursor:pointer;position:relative;" t-att-value="data.id"
                         t-on-click="_onClickToMessage">

                        <div style="width:30px">
                            <i style="margin:8px" class="fa fa-user"/>
                        </div>

                        <div style="margin-left: 20px;width: 250px">
                            <div style="display:flex;justify-content:space-between;">
                                <span t-esc="data.name"/>
                                <t t-if="data.count > 0">
                                    <span style="background-color:#04AA6D;color:white;border-radius:50%;
                                          width:18px;height:18px;font-size:10px;text-align:center;
                                          line-height:18px;" t-esc="data.count"/>
                                </t>
                            </div>
                            <small style="color:#9c9a97; white-space: pre-line;" t-raw="data.message_body"/>
                        </div>
                    </div>
                </t>
            </t>
        </div>

        <!-- Channel Messages -->
        <div id="all_channels" style="display:none">
            <t t-foreach="state.data" t-as="data" t-key="data.id">
                <t t-if="data.type == 'channel'">
                    <div style="background-color: #ffffcc;border-left: 6px solid #ffeb3b;
                        margin-bottom: 15px;padding: 4px 12px;display:flex;cursor:pointer;position:relative;" t-att-value="data.id"
                         t-on-click="_onClickToMessage">

                        <div style="width:30px">
                            <i style="margin:8px" class="fa fa-users"/>
                        </div>

                        <div style="margin-left: 20px;width: 250px">
                            <div style="display:flex;justify-content:space-between;">
                                <span t-esc="data.name"/>
                                <t t-if="data.count > 0">
                                    <span style="background-color:#ffeb3b;color:black;border-radius:50%;
                                          width:18px;height:18px;font-size:10px;text-align:center;
                                          line-height:18px;" t-esc="data.count"/>
                                </t>
                            </div>
                            <small style="color:#9c9a97; white-space: pre-line;" t-raw="data.message_body"/>
                        </div>
                    </div>
                </t>
            </t>
        </div>
    </div>`;