/** @odoo-module */
import { _t } from "@web/core/l10n/translation";
import { ThreadService } from "@mail/core/common/thread_service";
import { prettifyMessageContent } from "@mail/utils/common/format";
import { patch } from "@web/core/utils/patch";
const FETCH_LIMIT = 30;

patch(ThreadService.prototype, {
    /**
     * @override
     * @param {import("models").Thread} thread
     */
     getFetchParams(thread) {
        if (thread.model === "discuss.channel") {
            return { channel_id: thread.id };
        }
        if (thread.type === "chatter") {
            return {
                thread_id: thread.id,
                thread_model: thread.model,
            };
        }
        return {};
    },

    async search(searchTerm, thread, before = false, searchDate=false,followerSearch_id=false) {
        const { messages, count } = await this.rpc(this.getFetchRoute(thread), {
            ...this.getFetchParams(thread),
            search_term: await prettifyMessageContent(searchTerm), // formatted like message_post
            before,
            search_date : searchDate,
            follower_search_id : followerSearch_id
        });
        return {
            count,
            loadMore: messages.length === FETCH_LIMIT,
            messages: this.store.Message.insert(messages, { html: true }),
        };
    }
})