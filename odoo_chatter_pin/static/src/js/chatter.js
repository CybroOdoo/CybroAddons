/** @odoo-module **/
import { useService } from "@web/core/utils/hooks";
import { Chatter } from "@mail/chatter/web_portal/chatter";
import { useEffect } from "@odoo/owl";
import { patch } from "@web/core/utils/patch";
import { MessageCardList } from "@mail/core/common/message_card_list";

patch(Chatter.prototype, {
    setup() {
        super.setup();
        this.orm = useService("orm");
        Object.assign(this.state, {
            showPinnedMessages: false,
        });
        useEffect(() => {
            this.initialLoad();
        }, () => [this.props.threadId, this.props.threadModel]);
    },

    async initialLoad() {
        if (!this.state.thread) {
            return;
        }
        await this.load(this.state.thread, ["messages"]);
        if (!this.state.thread?.messages) {
            return;
        }

        try {
            const pinnedMessages = await this.orm.searchRead(
                "mail.message",
                [
                    ["is_pinned", "=", true],
                    ["model", "=", this.props.threadModel],
                    ["res_id", "=", this.props.threadId],
                ],
                ["id"]
            );

            const pinnedIds = new Set(pinnedMessages.map((msg) => msg.id));
            for (const msg of this.state.thread.messages) {
                msg.is_pinned = pinnedIds.has(msg.id);
            }
            this.state.thread.messages = [...this.state.thread.messages];
        } catch (error) {
            console.error("Error loading pinned messages:", error);
        }
    },

    get pinnedMessages() {
        const pinned = this.state.thread?.messages?.filter((msg) => msg.is_pinned) ?? [];
        return pinned;
    },

    togglePinnedMessages() {
        this.state.showPinnedMessages = !this.state.showPinnedMessages;
    },

    async load(thread, requestList) {
        if (!thread.id || !this.state.thread?.eq(thread)) {
            return;
        }
        await thread.fetchData(requestList);
    },
});
Chatter.components = { ...Chatter.components, MessageCardList };