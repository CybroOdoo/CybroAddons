/** @odoo-module **/

import { rpc } from "@web/core/network/rpc";
import { patch } from "@web/core/utils/patch";
import { Store } from "@mail/core/common/store_service";
import { prettifyMessageContent } from "@mail/utils/common/format";

patch(Store.prototype, {
    /**
     * @override
     */
    async search(searchTerm, thread, before = false, searchDate = false, followerSearchId = false) {
        console.log("ChatterFilter: Store.search called", {
            searchTerm,
            threadId: thread.id,
            threadModel: thread.model,
            before,
            searchDate,
            followerSearchId
        });

        if (!searchTerm && !searchDate && !followerSearchId) {
            console.log("ChatterFilter: No search criteria provided, returning null");
            return null;
        }

        const route = thread.getFetchRoute();
        const params = {
            ...thread.getFetchParams(),
            limit: this.FETCH_LIMIT,
            offset: before ? thread.messages.length : 0,
        };

        // Add search parameters if they exist
        if (searchTerm) {
            params.search_term = searchTerm.trim();
        }
        if (searchDate) {
            params.search_date = searchDate;
        }
        if (followerSearchId) {
            params.follower_search_id = followerSearchId;
        }

        console.log("ChatterFilter: RPC Call", { route, params });

        try {
            const response = await rpc(route, params);
            console.log("ChatterFilter: RPC Result", { 
                count: response.count, 
                messages_length: response.messages?.length || 0 
            });

            // Process messages if any
            if (response.messages && response.messages.length > 0) {
                const messages = this.Message.insert(response.messages);
                return {
                    count: response.count,
                    loadMore: response.messages.length === this.FETCH_LIMIT,
                    messages: messages,
                };
            }
            
            return {
                count: 0,
                loadMore: false,
                messages: [],
            };
        } catch (error) {
            console.error("ChatterFilter: RPC Error", error);
            throw error;
        }
    }
});