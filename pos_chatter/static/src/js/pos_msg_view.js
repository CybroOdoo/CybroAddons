/** @odoo-module **/
import PosComponent from 'point_of_sale.PosComponent';
import ajax from 'web.ajax';
import { ChatMsgView } from "./pos_chat_view"
export class PosMsgView extends PosComponent {
    setup(){
        super.setup(...arguments);
        this.ChatWindow = new ChatMsgView();
        var self = this
        ajax.jsonRpc('/pos_systray/message_data', 'call').then(function(data){
            self.state = owl.useState({
                'open':false,
                'data': data
            })
        })
    }
    /** for opening the chat window for the corresponding channel*/
    _onClickToMessage(ev){
        var channel_id = ev.currentTarget.getAttribute("value")
        this.ChatWindow.open_window(channel_id);
        this.close_window();
    }
    /** for click function for navbar*/
    _onClickAllMessage(){
        this.el.querySelector('#all_message').style.display = "block"
        this.el.querySelector('#all_chat').style.display = "none"
        this.el.querySelector('#all_channels').style.display = "none"
        this.el.querySelector('#all_message_button').style.color = "#000"
        this.el.querySelector('#all_chat_button').style.color = "#9c9a97"
        this.el.querySelector('#all_channels_button').style.color = "#9c9a97"
    }
    /** for click function for navbar*/
    _onClickAllChannels(){
        this.el.querySelector('#all_message').style.display = "none"
        this.el.querySelector('#all_chat').style.display = "none"
        this.el.querySelector('#all_channels').style.display = "block"
        this.el.querySelector('#all_message_button').style.color = "#9c9a97"
        this.el.querySelector('#all_chat_button').style.color = "#9c9a97"
        this.el.querySelector('#all_channels_button').style.color = "#000"
    }
    /** for click function for navbar*/
    _onClickAllChat(){
        this.el.querySelector('#all_message').style.display = "none"
        this.el.querySelector('#all_chat').style.display = "block"
        this.el.querySelector('#all_channels').style.display = "none"
        this.el.querySelector('#all_message_button').style.color = "#9c9a97"
        this.el.querySelector('#all_chat_button').style.color = "#000"
        this.el.querySelector('#all_channels_button').style.color = "#9c9a97"
    }
    /** for opening the chat list window*/
    open_window(){
        this.mount(document.body)
        this.state.open = true;
    }
    /** for closing the chat list window*/
    close_window(){
        this.unmount()
        this.state.open = false;
    }
    /** for checking the window is opened or not*/
    toggle(){
        if(this.state.open){
            this.close_window();
        }else{
            this.open_window();
        }
    }
}
PosMsgView.template = 'PosMsgView';
