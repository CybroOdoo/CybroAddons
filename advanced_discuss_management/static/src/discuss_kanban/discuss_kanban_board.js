import { DiscussAvatar } from "@mail/core/common/discuss_avatar";
import { MENU_TABS } from "@mail/core/public_web/messaging_menu/messaging_menu_model";

import { Component } from "@odoo/owl";

import { _t } from "@web/core/l10n/translation";
import { normalize } from "@web/core/l10n/utils";
import { useService } from "@web/core/utils/hooks";

/**
 * Kanban board shown in the Discuss content area when no conversation is selected.
 * It displays the conversations of the active sidebar tab (Chats, Channels, Meetings)
 * as cards, honouring the filter chip and search term of the sidebar.
 */
export class DiscussKanbanBoard extends Component {
    static template = "advanced_discuss_management.DiscussKanbanBoard";
    static components = { DiscussAvatar };

    setup() {
        super.setup();
        this.store = useService("mail.store");
    }

    get sidebarState() {
        return this.store.discuss.sidebarState;
    }

    get tab() {
        return this.sidebarState.activeTab;
    }

    get channels() {
        const state = this.sidebarState;
        const filters = [...state.activePluginFilters];
        if (state.selectedFilter) {
            filters.push(state.selectedFilter);
        }
        let channels = this.tab.channels.filter((c) =>
            filters.every((f) => !f.includesChannel || f.includesChannel(c))
        );
        if (state.searchTerm) {
            const term = normalize(state.searchTerm);
            channels = channels.filter((c) => normalize(c.displayName).includes(term));
        }
        return this.tab.getSortedChannels(state.selectedFilter, channels);
    }

    get canStartMeeting() {
        return this.store.self_user?.share === false;
    }

    get isChatTab() {
        return this.tab.id === MENU_TABS.CHAT;
    }

    get emptyText() {
        if (this.sidebarState.searchTerm) {
            return _t('No results for "%s".', this.sidebarState.searchTerm);
        }
        return this.tab.emptyState?.title ?? _t("Nothing here yet.");
    }

    /** @param {import("models").DiscussChannel} channel */
    previewText(channel) {
        const message = channel.newestPersistentOfAllMessage;
        if (!message) {
            return _t("This is the start of your conversation");
        }
        return message.previewText;
    }

    /** @param {import("models").DiscussChannel} channel */
    counter(channel) {
        return channel.importantCounter || channel.needactionCounter || 0;
    }

    /** @param {import("models").DiscussChannel} channel */
    onClickCard(channel) {
        channel.open({ focus: true, fromMessagingMenu: true, bypassCompact: true });
    }

    onClickMeeting() {
        this.store.requestStartMeeting();
    }

    onClickLoadMore() {
        this.tab.loadMore({
            filter: this.sidebarState.selectedFilter,
            pluginFilters: this.sidebarState.activePluginFilters,
        });
    }
}
