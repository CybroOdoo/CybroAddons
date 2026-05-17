/** @odoo-module **/
import { patch } from "@web/core/utils/patch";
import { MessagingMenu } from "@mail/core/public_web/messaging_menu";
import { DiscussSidebar } from "@mail/core/public_web/discuss_sidebar";
import { DiscussSidebarMailboxes } from "@mail/core/web/discuss_sidebar_mailboxes";
import { DiscussSearch } from "@mail/core/public_web/discuss_search";
import { Mp3Encoder } from "@mail/discuss/voice_message/common/mp3_encoder";
import { onMounted, onWillStart, useRef } from "@odoo/owl";
import { useState } from "@odoo/owl";
import { rpc } from "@web/core/network/rpc";
import { DiscussSidebarChannel } from "@mail/discuss/core/public_web/discuss_sidebar_categories";
import { DiscussSidebarCategory } from "@mail/discuss/core/public_web/discuss_sidebar_categories";
import { cleanTerm } from "@mail/utils/common/format";
import { useService } from "@web/core/utils/hooks";
import { _t } from "@web/core/l10n/translation";

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
        this.discusscorePublicWebService = useService("discuss.core.public.web");
        this.actionService = useService("action");
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
        onMounted(() => this.sidebar());
    },

    sidebar(){
    var self = this
        rpc('/select_user_image', {}).then((result) => {
    if (!this.root.el) return;
    const image = document.createElement('div');
    image.innerHTML = `<img class="o_Composer_currentPartner rounded-circle o_object_fit_cover"
        style="margin-top:21px;margin-left:10px;width:45px;height:45px;"
        src="data:image/png;base64,${result}">`;
    this.root.el.querySelector('#img')?.appendChild(image);
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
    toggleCategory(category) {
        category.open = !category.open;
        this.discusscorePublicWebService.broadcastCategoryState(category);
    },
    openCategory(category) {
        if (category.id === "channels") {
            this.actionService.doAction({
                name: _t("Public Channels"),
                type: "ir.actions.act_window",
                res_model: "discuss.channel",
                views: [
                    [false, "kanban"],
                    [false, "list"],
                    [false, "form"],
                ],
                domain: [
                    ["channel_type", "=", "channel"],
                    ["parent_channel_id", "=", false],
                ],
            });
        }
    },
    addToCategory(category) {
        // Standard Odoo 18 behavior for adding to category
        if (category.id === "channels") {
            this.actionService.doAction({
                name: _t("Create a Public Channel"),
                type: "ir.actions.act_window",
                res_model: "discuss.channel",
                views: [[false, "form"]],
                target: "new",
                context: { default_channel_type: "channel" },
            });
        } else if (category.id === "direct_messages") {
             this.actionService.doAction({
                name: _t("Open Chat"),
                type: "ir.actions.act_window",
                res_model: "mail.compose.message",
                views: [[false, "form"]],
                target: "new",
            });
        }
    },
    onClickStartMeeting(ev) {
        this.store.startMeeting();
    },
});

DiscussSidebar.components = {
    ...DiscussSidebar.components,
     DiscussSidebarMailboxes, DiscussSearch, MessagingMenu, DiscussSidebarCategory, Mp3Encoder, DiscussSidebarChannel
};
