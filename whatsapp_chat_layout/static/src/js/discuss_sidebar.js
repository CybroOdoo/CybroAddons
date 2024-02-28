/** @odoo-module **/
import { patch } from "@web/core/utils/patch";
import { DiscussSidebar } from "@mail/core/web/discuss_sidebar";
import { DiscussSidebarMailboxes } from "@mail/core/web/discuss_sidebar_mailboxes";
import { DiscussSidebarStartMeeting } from "@mail/discuss/call/web/discuss_sidebar_start_meeting";
import { ChannelSelector } from "@mail/discuss/core/web/channel_selector";
import { VoiceRecorder } from "@mail/discuss/voice_message/common/voice_recorder";
import { onMounted, onWillStart, useRef } from "@odoo/owl";
import { useState } from "@odoo/owl";
import { jsonrpc } from "@web/core/network/rpc_service";
import { DiscussSidebarCategories } from "@mail/discuss/core/web/discuss_sidebar_categories";

patch(DiscussSidebar.prototype, {
setup() {
         super.setup();
        this.root = useRef("root")
        this.state = useState({ sidebar: 'channels' , chat:'chats'});
        onWillStart(async () => {
        await jsonrpc('/select_color', {}).then(function(result) {
            console.log('1111111111111111111111')
            const root = document.documentElement;
            console.log(root,'1111111111111111111111')

            if (result.background_color !== false){
                root.style.setProperty("--background-color",result.background_color);
            }
            })
        });
        onMounted(this.sidebar)
    },
    sidebar(){
    var self = this
        jsonrpc('/select_user_image', {}).then(function(result) {
        let image = document.createElement('div')
        image.innerHTML = '<img class="o_Composer_currentPartner rounded-circle o_object_fit_cover"style="margin-top: 21px;margin-left: 10px;width: 45px;height: 45px;"src="data:image/png;base64,' + result + '">'
        self.root.el.querySelector('#img').appendChild(image);
        });
    },
    _onClickMail(ev) {// Click function of mail button
        this.root.el.querySelector('.mail').classList.remove("d-none");
        this.root.el.querySelector('.channel').classList.add("d-none");
        this.root.el.querySelector('.chat').classList.add("d-none");
    },
    _onClickChat(ev) {// Click function of chat button
        this.root.el.querySelector('.chat').classList.remove("d-none");
        this.root.el.querySelector('.mail').classList.add("d-none");
        this.root.el.querySelector('.channel').classList.add("d-none");
        this.state.sidebarChannel = 'chat'
    },
    _onClickChannel(ev) {// Click function of channel button
        this.root.el.querySelector('.channel').classList.remove("d-none");
        this.root.el.querySelector('.mail').classList.add("d-none");
        this.root.el.querySelector('.chat').classList.add("d-none");
                this.state.sidebarChat = 'channel'
    },
});

DiscussSidebar.components = {
    ...DiscussSidebar.components,
    DiscussSidebarMailboxes,DiscussSidebarCategories,DiscussSidebarStartMeeting,VoiceRecorder,ChannelSelector
};
