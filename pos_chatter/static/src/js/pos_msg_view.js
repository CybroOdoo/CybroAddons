import { Component, mount, xml, onMounted, onWillUnmount, proxy, signal } from "@odoo/owl";
import { rpc } from "@web/core/network/rpc";
import { ChatMsgView } from "./pos_chat_view";

let isPageNavigating = false;
window.addEventListener("beforeunload", () => {
    isPageNavigating = true;
});
window.addEventListener("pagehide", () => {
    isPageNavigating = true;
});

export class PosMsgView extends Component {
    root = signal.ref();

    setup() {
        super.setup();
        this.unmounted = false;
        this.clickOutsideListener = null;

        this.state = proxy({
            activeTab: "all",
            data: [],
            counts: {
                all: 0,
                chat: 0,
                channels: 0
            }
        });

        onMounted(() => {
            this.render_msg_view();
            setTimeout(() => {
                if (this.unmounted) return;
                this.clickOutsideListener = (ev) => {
                    const icon = document.querySelector("#pos_systray_chatter_icon");
                    const rootEl = this.root() || document.querySelector(".pos_systray_template");
                    if (
                        rootEl &&
                        !rootEl.contains(ev.target) &&
                        (!icon || !icon.contains(ev.target))
                    ) {
                        if (this.props.onClose) {
                            this.props.onClose();
                        } else {
                            rootEl.remove();
                        }
                    }
                };
                window.addEventListener("click", this.clickOutsideListener, true);
            }, 100);
        });

        onWillUnmount(() => {
            this.unmounted = true;
            if (this.clickOutsideListener) {
                window.removeEventListener("click", this.clickOutsideListener, true);
            }
        });
    }

    /** Fetch all chat messages */
    async render_msg_view() {
        if (this.unmounted || isPageNavigating) return;
        try {
            const data = await rpc("/pos_systray/message_data");
            if (this.unmounted || isPageNavigating) return;

            const message_list = (data || []).map((message) => {
                const parser = new DOMParser();
                const parsedHtml = parser.parseFromString(message.message_body || "", "text/html");
                const plainText = parsedHtml.documentElement.textContent || "";

                return {
                    id: message.id,
                    type: message.type,
                    name: message.name,
                    message_body: plainText,
                    count: message.count || 0,
                };
            });

            const counts = {
                all: message_list.reduce((sum, msg) => sum + msg.count, 0),
                chat: message_list.filter(m => m.type === 'chat').reduce((sum, msg) => sum + msg.count, 0),
                channels: message_list.filter(m => m.type === 'channel').reduce((sum, msg) => sum + msg.count, 0),
            };

            this.state.data = message_list;
            this.state.counts = counts;
        } catch (error) {
            if (!this.unmounted && !isPageNavigating && error?.name !== "ConnectionLostError") {
                console.error("Failed to fetch message data:", error);
            }
        }
    }

    _onClickAllMessage() {
        this.state.activeTab = "all";
    }

    _onClickAllChannels() {
        this.state.activeTab = "channels";
    }

    _onClickAllChat() {
        this.state.activeTab = "chat";
    }

    /** Open chat view */
    _onClickToMessage(ev) {
        const channel_id = ev.currentTarget.getAttribute("value");
        if (!channel_id || isNaN(parseInt(channel_id))) {
            console.error("Invalid channel_id:", channel_id);
            return;
        }

        const parsedChannelId = parseInt(channel_id);

        if (this.props.onOpenChat) {
            this.props.onOpenChat(parsedChannelId);
        } else {
            // Fallback for standalone mount
            const container = this.root() || document.querySelector(".pos_systray_template");
            if (container) {
                container.remove();
            }
            try {
                mount(ChatMsgView, document.body, { env: this.env, props: { channel_id: parsedChannelId } });
            } catch (error) {
                console.error("Failed to open chat:", error);
            }
        }
    }
}

PosMsgView.template = xml`
    <div class="pos_systray_template" t-ref="this.root"
        style="height:auto;width:350px;background-color:#f3f3f3;position:fixed;right:5px;top:49px;padding:10px;margin:40px 14px;z-index: 1000;border-radius:8px;box-shadow:0 4px 12px rgba(0,0,0,0.15);">

        <div style="display:flex;height: 27px;position:relative;">
            <div style="display:flex;">
                <p id="all_message_button"
                   t-att-style="this.state.activeTab === 'all' ? 'margin-left:10px;cursor: pointer;color:#000;font-weight:bold;' : 'margin-left:10px;cursor: pointer;color:#9c9a97;'"
                   t-on-click="this._onClickAllMessage">All</p>
                <p id="all_chat_button"
                   t-att-style="this.state.activeTab === 'chat' ? 'margin-left:10px;cursor: pointer;color:#000;font-weight:bold;' : 'margin-left:10px;cursor: pointer;color:#9c9a97;'"
                   t-on-click="this._onClickAllChat">Chat</p>
                <p id="all_channels_button"
                   t-att-style="this.state.activeTab === 'channels' ? 'margin-left:10px;cursor: pointer;color:#000;font-weight:bold;' : 'margin-left:10px;cursor: pointer;color:#9c9a97;'"
                   t-on-click="this._onClickAllChannels">Channels</p>
            </div>

            <!-- Count badges with exact positioning from image -->
            <span t-if="this.state.counts.all > 0"
                  style="position:absolute;right:220px;top:-18px;background:#2196F3;color:white;border-radius:50%;
                  width:18px;height:18px;font-size:10px;text-align:center;line-height:18px;"
                  t-out="this.state.counts.all"/>

            <span t-if="this.state.counts.chat > 0"
                  style="position:absolute;right:267px;top:-19px;background:#04AA6D;color:white;border-radius:50%;
                  width:18px;height:18px;font-size:10px;text-align:center;line-height:18px;"
                  t-out="this.state.counts.chat"/>

            <span t-if="this.state.counts.channels > 0"
                  style="position:absolute;right:302px;top:-19px;background:#ffeb3b;color:black;border-radius:50%;
                  width:18px;height:18px;font-size:10px;text-align:center;line-height:18px;"
                  t-out="this.state.counts.channels"/>
        </div>

        <hr style="margin:8px 0;"/>

        <!-- All Messages -->
        <div id="all_message" t-att-style="this.state.activeTab === 'all' ? 'display:block' : 'display:none'">
            <t t-foreach="this.state.data" t-as="data" t-key="data.id">
                <div style="background-color: #e7f3fe;border-left: 6px solid #2196F3;
                margin-bottom: 15px;padding: 4px 12px;display:flex;align-items:center;cursor:pointer;position:relative;" t-att-value="data.id"
                    t-on-click="this._onClickToMessage">

                    <div style="width:30px;display:flex;justify-content:center;">
                        <t t-if="data.type == 'channel'">
                            <i class="oi oi-fw" data-icon="group"/>
                        </t>
                        <t t-elif="data.type == 'sms_failure'">
                            <i class="oi oi-fw" data-icon="warning"/>
                        </t>
                        <t t-else="">
                            <i class="oi oi-fw" data-icon="person"/>
                        </t>
                    </div>

                    <div style="margin-left: 15px;width: 250px">
                        <div style="display:flex;justify-content:space-between;">
                            <span t-out="data.name"/>
                            <t t-if="data.count > 0">
                                <span style="background-color:#2196F3;color:white;border-radius:50%;
                                      width:18px;height:18px;font-size:10px;text-align:center;
                                      line-height:18px;" t-out="data.count"/>
                            </t>
                        </div>
                        <small style="color:#9c9a97; white-space: pre-line;" t-out="data.message_body"/>
                    </div>
                </div>
            </t>
        </div>

        <!-- Chat Messages -->
        <div id="all_chat" t-att-style="this.state.activeTab === 'chat' ? 'display:block' : 'display:none'">
            <t t-foreach="this.state.data" t-as="data" t-key="data.id">
                <t t-if="data.type == 'chat'">
                    <div style="background-color: #ddffdd;border-left: 6px solid #04AA6D;
                    margin-bottom: 15px;padding: 4px 12px;display:flex;align-items:center;cursor:pointer;position:relative;" t-att-value="data.id"
                         t-on-click="this._onClickToMessage">

                        <div style="width:30px;display:flex;justify-content:center;">
                            <i class="oi oi-fw" data-icon="person"/>
                        </div>

                        <div style="margin-left: 15px;width: 250px">
                            <div style="display:flex;justify-content:space-between;">
                                <span t-out="data.name"/>
                                <t t-if="data.count > 0">
                                    <span style="background-color:#04AA6D;color:white;border-radius:50%;
                                          width:18px;height:18px;font-size:10px;text-align:center;
                                          line-height:18px;" t-out="data.count"/>
                                </t>
                            </div>
                            <small style="color:#9c9a97; white-space: pre-line;" t-out="data.message_body"/>
                        </div>
                    </div>
                </t>
            </t>
        </div>

        <!-- Channel Messages -->
        <div id="all_channels" t-att-style="this.state.activeTab === 'channels' ? 'display:block' : 'display:none'">
            <t t-foreach="this.state.data" t-as="data" t-key="data.id">
                <t t-if="data.type == 'channel'">
                    <div style="background-color: #ffffcc;border-left: 6px solid #ffeb3b;
                        margin-bottom: 15px;padding: 4px 12px;display:flex;align-items:center;cursor:pointer;position:relative;" t-att-value="data.id"
                         t-on-click="this._onClickToMessage">

                        <div style="width:30px;display:flex;justify-content:center;">
                            <i class="oi oi-fw" data-icon="group"/>
                        </div>

                        <div style="margin-left: 15px;width: 250px">
                            <div style="display:flex;justify-content:space-between;">
                                <span t-out="data.name"/>
                                <t t-if="data.count > 0">
                                    <span style="background-color:#ffeb3b;color:black;border-radius:50%;
                                          width:18px;height:18px;font-size:10px;text-align:center;
                                          line-height:18px;" t-out="data.count"/>
                                </t>
                            </div>
                            <small style="color:#9c9a97; white-space: pre-line;" t-out="data.message_body"/>
                        </div>
                    </div>
                </t>
            </t>
        </div>
    </div>`;
