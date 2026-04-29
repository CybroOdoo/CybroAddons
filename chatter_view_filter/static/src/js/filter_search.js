/** @odoo-module **/
import { useState, onWillUnmount, onWillUpdateProps } from '@odoo/owl';
import { useService } from "@web/core/utils/hooks";
import { patch } from "@web/core/utils/patch";
import { useSequential } from "@mail/utils/common/hooks";
import { DateTimeInput } from "@web/core/datetime/datetime_input";
import { useVisible } from "@mail/utils/common/hooks";
import { SearchMessagesPanel } from "@mail/core/common/search_messages_panel";
import { SearchMessageInput } from "@mail/core/common/search_message_input";
import { Dropdown } from "@web/core/dropdown/dropdown";
import { DropdownItem } from "@web/core/dropdown/dropdown_item";
import { Chatter } from "@mail/chatter/web_portal/chatter";
import { searchHighlight } from "@mail/core/common/message_search_hook";

export function useMessageSearch(thread) {
    const store = useService("mail.store");
    const sequential = useSequential();
    const state = useState({
        thread,
        async search(before = false) {
            console.log("ChatterFilter: useMessageSearch.search triggered", {
                searchTerm: this.searchTerm,
                searchDate: this.searchDate,
                followerSearch_id: this.followerSearch_id,
                before
            });

            // Only proceed if we have at least one search criteria
            if (this.searchTerm || this.searchDate || this.followerSearch_id) {
                this.searching = true;
                try {
                    const data = await sequential(() =>
                        store.search(
                            this.searchTerm || "",
                            this.thread,
                            before,
                            this.searchDate,
                            this.followerSearch_id
                        )
                    );

                    console.log("ChatterFilter: search data received", data);

                    // If no data returned, reset the search
                    if (!data) {
                        this.searching = false;
                        this.messages = [];
                        this.count = 0;
                        this.loadMore = false;
                        this.searched = true;
                        return;
                    }

                    const { count, loadMore, messages } = data;
                    this.searched = true;
                    this.searching = false;
                    this.count = count;
                    this.loadMore = loadMore;

                    // Update messages based on search direction
                    if (before) {
                        this.messages = [...messages, ...this.messages];
                    } else {
                        this.messages = [...messages];
                    }

                    console.log("ChatterFilter: messages updated", this.messages.length);
                } catch (e) {
                    console.error("ChatterFilter: search failed", e);
                    this.searching = false;
                    // Show error to user if needed
                    this.messages = [];
                    this.count = 0;
                    this.loadMore = false;
                }
            } else {
                // If no search criteria, clear the search
                this.clear();
            }
        },
        count: 0,
        clear() {
            console.log("ChatterFilter: clear called");
            this.messages = [];
            this.searched = false;
            this.searching = false;
            this.searchTerm = "";
            this.searchDate = "";
            this.followerSearch_id = "";
            this.count = 0;
            this.loadMore = false;
        },
        loadMore: false,
        messages: [],
        searchTerm: "",
        searchDate: "",
        followerSearch_id: "",
        searched: false,
        searching: false,
        highlight: (target) => state.searchTerm ? searchHighlight(state.searchTerm, target) : target,
    });
    onWillUnmount(() => {
        state.clear();
    });
    return state;
}

patch(Chatter.prototype, {
    setup() {
        super.setup();
        this.messageSearch = useMessageSearch(this.state.thread);
    },
});

patch(SearchMessagesPanel.prototype, {
    setup() {
        super.setup();
        console.log("ChatterFilter: SearchMessagesPanel setup", this.props.thread.id);
        this.messageSearch = useMessageSearch(this.props.thread);

        onWillUpdateProps((nextProps) => {
            if (this.props.thread.id !== nextProps.thread.id) {
                console.log("ChatterFilter: Thread changed, resetting search");
                this.messageSearch.clear();
            }
        });
    },
});

patch(SearchMessageInput.prototype, {
    setup() {
        super.setup();
        this.orm = useService("orm");
        Object.assign(this.state, {
            searchDate: "",
        });

        this.loadMoreState = useVisible("load-more", () => {
            if (this.loadMoreState.isVisible && this.props.messageSearch.loadMore) {
                this.props.messageSearch.search(true);
            }
        });
    },

    async onAddUserFilterClick(followerId) {
        console.log("ChatterFilter: Follower clicked", followerId);
        const [partner_id, partner_name] = await this.orm.call("mail.followers", "get_partner", [followerId], {});
        console.log("ChatterFilter: Partner retrieved", { partner_id, partner_name });

        this.props.messageSearch.followerSearch_id = partner_id;
        this.props.messageSearch.searchTerm = "";
        this.state.searchTerm = partner_name;

        await this.props.messageSearch.search();
    },

    onDateChange(ev) {
        this.state.searchDate = ev.target.value;
    },

    clearDate() {
        this.state.searchDate = "";
        if (this.props.messageSearch.searchDate) {
            this.props.messageSearch.searchDate = "";
            this.props.messageSearch.search();
        }
    },

    clearFilters() {
        this.state.searchTerm = "";
        this.state.searchDate = "";
        this.props.messageSearch.clear();
    },

    async DateMessageSearch() {
        console.log("ChatterFilter: Date search clicked", this.state.searchDate);
        this.props.messageSearch.searchDate = this.state.searchDate;
        this.props.messageSearch.searchTerm = "";
        this.state.searchTerm = this.state.searchDate;

        await this.props.messageSearch.search();
    },
});

Object.assign(SearchMessageInput, {
    components: {
        ...SearchMessageInput.components,
        Dropdown,
        DropdownItem,
        DateTimeInput,
    },
});
