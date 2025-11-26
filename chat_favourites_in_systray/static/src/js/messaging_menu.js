/** @odoo-module **/
import { MessagingMenu } from "@mail/core/web/messaging_menu";
import { patch } from "@web/core/utils/patch";
import { jsonrpc } from "@web/core/network/rpc_service";
import { session } from "@web/session";
import { useState } from "@odoo/owl";

patch(MessagingMenu.prototype, {
    async setup() {
        super.setup();
        this.state = useState({
            favoriteChannels: [],
            matchedFavouriteChats: [],
        });

        // Fetch favorite channels for the current user
        await this._loadFavoriteChannels();
    },

    async _loadFavoriteChannels() {
        const userDomain = [['id', '=', session.uid]];
        const userFields = ['mail_channel_ids'];

        const userData = await jsonrpc('/web/dataset/call_kw/res.users/search_read', {
            model: 'res.users',
            method: 'search_read',
            args: [userDomain, userFields],
            kwargs: {},
        });

        if (userData?.[0]?.mail_channel_ids?.length) {
            const channelIds = userData[0].mail_channel_ids;
            const channelDomain = [['id', 'in', channelIds]];

            const allFields = await jsonrpc('/web/dataset/call_kw/discuss.channel/fields_get', {
                model: 'discuss.channel',
                method: 'fields_get',
                args: [],
                kwargs: {},
            });

            const channelFields = Object.keys(allFields);

            const channelData = await jsonrpc('/web/dataset/call_kw/discuss.channel/search_read', {
                model: 'discuss.channel',
                method: 'search_read',
                args: [channelDomain, channelFields],
                kwargs: {},
            });

            this.state.favoriteChannels = channelData.map(channel => ({
                ...channel,
                body: JSON.stringify(channel),
            }));
        }
    },

    async onClickFavouriteTab() {
        await this._loadFavoriteChannels();
        this.store.discuss.activeTab = 'favourite';
        const records = this.store.Thread.records;
        const favouriteChats = Object.values(records).filter(thread =>
            thread.model === "discuss.channel" && thread.favourite
        );
        const favouriteChannelIds = this.state.favoriteChannels.map(channel => channel.id);
        this.state.matchedFavouriteChats = favouriteChats.filter(chat =>
            favouriteChannelIds.includes(chat.id)
        );
    },
});
