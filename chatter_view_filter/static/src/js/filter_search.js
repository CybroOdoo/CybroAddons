/** @odoo-module **/
import { Component, useState, onWillUnmount } from '@odoo/owl';
import { useService } from "@web/core/utils/hooks";
import { patch } from "@web/core/utils/patch";
import { useSequential } from "@mail/utils/common/hooks";
import { DateTimeInput } from "@web/core/datetime/datetime_input";
import { useVisible } from "@mail/utils/common/hooks";
import { SearchMessagesPanel } from "@mail/core/common/search_messages_panel";
import { Dropdown } from "@web/core/dropdown/dropdown";
import { DropdownItem } from "@web/core/dropdown/dropdown_item";
import { searchHighlight } from "@mail/core/common/message_search_hook";
export function useMessageSearch(thread) {
    const threadService = useService("mail.thread");
    const sequential = useSequential();
    const state = useState({
        thread,
        async search(before = false) {
            if (this.searchTerm) {
                this.searching = true;
                const data = await sequential(() =>

                    threadService.search(this.searchTerm, this.thread, before,
                                this.searchDate, this.followerSearch_id)
                );
                if (!data) {
                    return;
                }
                const { count, loadMore, messages } = data;
                this.searched = true;
                this.searching = false;
                this.count = count;
                this.loadMore = loadMore;
                if (before) {
                    this.messages.push(...messages);
                } else {
                    this.messages = messages;
                }
            } else {
                this.clear();
            }
        },
        count: 0,
        clear() {
            this.messages = [];
            this.searched = false;
            this.searching = false;
            this.searchTerm = undefined;
        },
        loadMore: false,
        /** @type {import('@mail/core/common/message_model').Message[]} */
        messages: [],
        /** @type {string|undefined} */
        searchTerm: undefined,
        searched: false,
        searching: false,
        /** @param {string} target */
        highlight: (target) => searchHighlight(state.searchTerm, target),
    });
    onWillUnmount(() => {
        state.clear();
    });
    return state;
}
patch(SearchMessagesPanel.prototype, {
    setup() {
        super.setup();
        this.store = useState(useService("mail.store"));
        this.orm = useService("orm");
        this.messageSearch = useMessageSearch(this.props.thread);
        this.threadService = useState(useService("mail.thread"));
        this.loadMoreState = useVisible("load-more", () => {
            if (this.loadMoreState.isVisible) {
                this.threadService.loadMoreFollowers(this.props.thread);
            }
        });
        onWillUnmount(() => {
        this.props.filterSearch = false
    });
    },

    async onAddUserFilterClick(follower, selfFollower){
        const follower_id = follower
        const [partner_id, partner_name] = await this.orm.call("mail.followers", "get_partner", [follower_id], {})
        this.props.followerSearch = partner_id
        this.messageSearch.followerSearch_id = this.props.followerSearch
        this.state.searchTerm = partner_name
        this.search()
    },
    onChanged(date){
            if (date){
                if (date.c.year && date.c.month && date.c.day) {
                    let month = date.c.month < 10 ? '0' + date.c.month : date.c.month;
                    let day = date.c.day < 10 ? '0' + date.c.day : date.c.day;

                    date = `${date.c.year}-${month}-${day}`;
                    this.props.date  = date
                    return date
                }
            }
    },

     async DateMessageSearch(){
        this.props.filterSearch = true
        this.messageSearch.searchDate = this.props.date
        this.state.searchTerm = this.props.date
        this.search()

    },
});

// Extend the components on the patched element
Object.assign(SearchMessagesPanel, {
    components: {
        ...SearchMessagesPanel.components, // Preserve existing components
        Dropdown,
        DropdownItem,
        DateTimeInput,
    },
});
