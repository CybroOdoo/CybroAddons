/** @odoo-module **/
import { patch } from "@web/core/utils/patch";
import { MessagingMenu } from "@mail/core/public_web/messaging_menu";
import { DiscussSidebar } from "@mail/core/public_web/discuss_sidebar";
import { DiscussSidebarMailboxes } from "@mail/core/web/discuss_sidebar_mailboxes";
import { ChannelSelector } from "@mail/discuss/core/web/channel_selector";
import { VoiceRecorder } from "@mail/discuss/voice_message/common/voice_recorder";
import { onMounted, onWillStart, useRef } from "@odoo/owl";
import { useState } from "@odoo/owl";
import { rpc } from "@web/core/network/rpc";
import { DiscussSidebarChannel } from "@mail/discuss/core/public_web/discuss_sidebar_categories";
import { DiscussSidebarCategory } from "@mail/discuss/core/public_web/discuss_sidebar_categories";
import { cleanTerm } from "@mail/utils/common/format";
import { useService } from "@web/core/utils/hooks";

patch(DiscussSidebar.prototype, {
setup() {
        super.setup();
        this.root = useRef("root")
        this.state = useState({
            sidebar: 'channels',
            chat: 'chats',
            quickSearchVal: "",
            floatingQuickSearchOpen: false
        });
        this.store = useState(useService("mail.store"));
        // Use the same filteredThreads logic as DiscussSidebarCategories
        this.filteredThreads = (threads) => {
            return threads.filter(
                (thread) =>
                    thread.displayInSidebar &&
                    (thread.parent_channel_id ||
                        !this.state.quickSearchVal ||
                        cleanTerm(thread.displayName).includes(cleanTerm(this.state.quickSearchVal)))
            );
        };

        onWillStart(async () => {
        await rpc('/select_color', {}).then(function(result) {
            const root = document.documentElement;
            if (result.background_color !== false){
                root.style.setProperty("--background-color",result.background_color);
            }
            })
        });
        onMounted(this.sidebar)
    },

    sidebar(){
    var self = this
        rpc('/select_user_image', {}).then(function(result) {
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
     DiscussSidebarMailboxes, ChannelSelector, MessagingMenu, DiscussSidebarCategory, VoiceRecorder, DiscussSidebarChannel
};
