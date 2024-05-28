/** @odoo-module **/
import { patch } from "@web/core/utils/patch";
import { DiscussSidebar } from "@mail/core/web/discuss_sidebar";
import { DiscussSidebarMailboxes } from "@mail/core/web/discuss_sidebar_mailboxes";
import { DiscussSidebarStartMeeting } from "@mail/discuss/call/web/discuss_sidebar_start_meeting";
import { ChannelSelector } from "@mail/discuss/core/web/channel_selector";
import { VoiceRecorder } from "@mail/discuss/voice_message/common/voice_recorder";
import { onMounted, onWillStart, useRef } from "@odoo/owl";
import { useState } from "@odoo/owl";
import { DiscussSidebarCategories } from "@mail/discuss/core/web/discuss_sidebar_categories";

patch(DiscussSidebar.prototype, {
setup() {
        super.setup();
        this.root = useRef("root")
        this.env.bus.addEventListener("HIDE:CHAT", () => {
            if( this.root.el.querySelector('.channel')){
                this.root.el.querySelector('.channel').classList.add("d-none");
                }
            this.root.el.querySelector('.mail').classList.add("d-none");
            this.root.el.querySelector('.chat').classList.add("d-none");
        })
        this.state = useState({sidebar: 'channels' , chat:'chats'});
        onMounted(() => {
      // Call the _onClickChannel function when the component is mounted
      this.sidebar;
      this._onClickChannel();
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

