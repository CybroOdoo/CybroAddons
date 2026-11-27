import { MessagingMenu } from "@mail/core/public_web/messaging_menu/messaging_menu";
import { MessagingMenuItem } from "@mail/core/public_web/messaging_menu/messaging_menu_item";

import { computed } from "@odoo/owl";

import { patch } from "@web/core/utils/patch";

/**
 * Local ids of the threads whose parent channel is also in the list.
 *
 * @param {import("models").DiscussChannel[]} channels
 * @returns {Set<string>}
 */
function getNestedThreadIds(channels) {
    const shownIds = new Set(channels.map((c) => c.localId));
    return new Set(
        channels
            .filter((c) => c.parent_channel_id && shownIds.has(c.parent_channel_id.localId))
            .map((c) => c.localId)
    );
}

/**
 * Move each thread right below its parent channel, keeping the sort order of the tab
 * among the channels and among the threads of a channel. A thread whose parent is not
 * in the list (e.g. "Thread" filter) stays where it is.
 *
 * @param {import("models").DiscussChannel[]} channels
 * @param {Set<string>} nestedIds
 */
function nestThreads(channels, nestedIds) {
    if (!nestedIds.size) {
        return channels;
    }
    const threadsByParentId = new Map();
    for (const channel of channels) {
        if (nestedIds.has(channel.localId)) {
            const parentId = channel.parent_channel_id.localId;
            if (!threadsByParentId.has(parentId)) {
                threadsByParentId.set(parentId, []);
            }
            threadsByParentId.get(parentId).push(channel);
        }
    }
    const result = [];
    for (const channel of channels) {
        if (!nestedIds.has(channel.localId)) {
            result.push(channel, ...(threadsByParentId.get(channel.localId) ?? []));
        }
    }
    return result;
}

patch(MessagingMenu.prototype, {
    setup() {
        super.setup(...arguments);
        if (!this.channels) {
            return;
        }
        const flatChannels = this.channels;
        this.admNestedThreadIds = computed(() => getNestedThreadIds(flatChannels()));
        this.channels = computed(() => nestThreads(flatChannels(), this.admNestedThreadIds()));
    },
});

patch(MessagingMenuItem.prototype, {
    /**
     * - Threads get `meeting_start_dt = false` from the server, and `false.toLocaleString()`
     *   is "false": only format an actual date. Nested threads use the plain name branch of
     *   the template, which shows this text as "@ <time>".
     * - A meeting started now has the same start time as the time shown on the right of the
     *   row (its first message / creation): don't show that time twice. A planned meeting
     *   keeps its "@ <start time>" label.
     *
     * @override
     */
    get meetingStartText() {
        const start = this.channel?.meeting_start_dt;
        if (!start) {
            return "";
        }
        const shownDatetime = this.notificationItemProps?.datetime;
        if (shownDatetime && start.hasSame(shownDatetime, "minute")) {
            return "";
        }
        return super.meetingStartText;
    },
    get attClass() {
        return {
            ...super.attClass,
            "o-adm-MessagingMenuItem-nested": Boolean(this.props.admNested),
        };
    },
});
