/** @odoo-module **/
import { jsonrpc } from "@web/core/network/rpc_service";
const { mount,xml, onMounted, useState, useRef} = owl;
import { ChatMsgView } from "./pos_chat_view"
export class PosMsgView extends owl.Component {
    setup(){
        super.setup()
        this.root = useRef("root")
        onMounted(this.render_msg_view)
        this.MsgWindow = new ChatMsgView();
        this.state = useState({
            'data': {}
        });
    }
    /** for getting all chat list */
    render_msg_view(data){
        var self = this
        jsonrpc('/pos_systray/message_data',).then(function(data){
            var message_list = []
            var messages = data
            $(messages).each(function(message){
                const htmlString = messages[message].message_body;
                const parser = new DOMParser();
                const parsedHtml = parser.parseFromString(htmlString, 'text/html');
                const plainText = parsedHtml.documentElement.textContent;
                message_list.push({
                    'id': messages[message].id,
                    'type': messages[message].type,
                    'name': messages[message].name,
                    'message_body': plainText
                })
            });
            self.state.data = message_list
        })
    }

    /** for click function for navbar*/
    _onClickAllMessage(){
        this.root.el.querySelector('#all_message').style.display = "block"
        this.root.el.querySelector('#all_chat').style.display = "none"
        this.root.el.querySelector('#all_channels').style.display = "none"
        this.root.el.querySelector('#all_message_button').style.color = "#000"
        this.root.el.querySelector('#all_chat_button').style.color = "#9c9a97"
        this.root.el.querySelector('#all_channels_button').style.color = "#9c9a97"
    }
    /** for click function for navbar*/
    _onClickAllChannels(){
        this.root.el.querySelector('#all_message').style.display = "none"
        this.root.el.querySelector('#all_chat').style.display = "none"
        this.root.el.querySelector('#all_channels').style.display = "block"
        this.root.el.querySelector('#all_message_button').style.color = "#9c9a97"
        this.root.el.querySelector('#all_chat_button').style.color = "#9c9a97"
        this.root.el.querySelector('#all_channels_button').style.color = "#000"
    }
    /** for click function for navbar*/
    _onClickAllChat(){
        this.root.el.querySelector('#all_message').style.display = "none"
        this.root.el.querySelector('#all_chat').style.display = "block"
        this.root.el.querySelector('#all_channels').style.display = "none"
        this.root.el.querySelector('#all_message_button').style.color = "#9c9a97"
        this.root.el.querySelector('#all_chat_button').style.color = "#000"
        this.root.el.querySelector('#all_channels_button').style.color = "#9c9a97"
    }
    /** On clicking the chat or channel open the corresponding chat view */
    _onClickToMessage(ev){
        var self = this
        var channel_id = ev.currentTarget.getAttribute("value")
        this.__owl__.remove()
        if($("#pos_chat_view").length == 0){
            this.schedule_dropdown = mount(ChatMsgView, document.body, {props: {
                channel_id
            }})
        }else if($("#pos_chat_view").length > 0){
            this.schedule_dropdown = mount(ChatMsgView, document.body, {props: {
                channel_id
            }})
        }
    }
}
PosMsgView.template =  xml`
    //template for pos messages list view
    <div class="pos_systray_template" t-ref="root"
    style="height:auto;width:350px;background-color:white;position:fixed;right:5px;top:49px;">
        <div style="display:flex;height: 27px;">
            <p style="margin-left:10px;cursor: pointer;" id="all_message_button"
               t-on-click="_onClickAllMessage">All</p>
            <p style="margin-left:10px;cursor: pointer;color:#9c9a97;" id="all_chat_button"
               t-on-click="_onClickAllChat">Chat</p>
            <p style="margin-left:10px;cursor: pointer;color:#9c9a97;" id="all_channels_button"
               t-on-click="_onClickAllChannels">Channels</p>
        </div>
        <hr/>
        <div id="all_message">
            <t t-foreach="state.data" t-as="data" t-key="data['id']">
            <div style="background-color: #e7f3fe;border-left: 6px solid #2196F3;
            margin-bottom: 15px;padding: 4px 12px;display:flex;cursor:pointer;" t-att-value="data['id']"
                 t-on-click="_onClickToMessage">
                    <div style="width:30px">
                        <t t-if="data['type'] == 'channel'">
                            <i style="margin:40%" class="fa fa-users"/>
                        </t>
                        <t t-else="">
                            <i style="margin:40%" class="fa fa-user"/>
                        </t>
                    </div>
                <div style="margin-left: 20px;width: 250px">
                        <span t-esc="data['name']"/>
                    <br/>
                    <small style="color:#9c9a97;" t-raw="data['message_body']"/>
                    </div>
            </div>
          </t>
        </div>
        <div id="all_chat" style="display:none">
            <t t-foreach="state.data" t-as="data" t-key="data['id']">
                <t t-if="data['type'] == 'chat'">
                    <div style="background-color: #ddffdd;  border-left: 6px solid #04AA6D;
                    margin-bottom: 15px;padding: 4px 12px;display:flex;cursor:pointer;" t-att-value="data['id']"
                         t-on-click="_onClickToMessage">
                        <div style="width:30px">
                            <i style="margin:8px" class="fa fa-user"/>
                        </div>
                        <div style="margin-left: 20px;width: 250px">
                            <span t-esc="data['name']"/>
                            <br/>
                            <small style="color:#9c9a97;" t-raw="data['message_body']"/>
                        </div>
                    </div>
                </t>
            </t>
        </div>
        <div id="all_channels" style="display:none">
             <t t-foreach="state.data" t-as="data" t-key="data['id']">
                <t t-if="data['type'] == 'channel'">
                    <div style="background-color: #ffffcc;border-left: 6px solid #ffeb3b;
                        margin-bottom: 15px;padding: 4px 12px;display:flex;cursor:pointer;" t-att-value="data['id']"
                         t-on-click="_onClickToMessage">
                        <div style="width:30px">
                                <i style="margin:8px" class="fa fa-users"/>
                        </div>
                        <div style="margin-left: 20px;width: 250px">
                                <span t-esc="data['name']"/>
                            <br/>
                            <small style="color:#9c9a97;" t-raw="data['message_body']"/>
                        </div>
                    </div>
                </t>
             </t>
        </div>
    </div>`
