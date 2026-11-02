/** @odoo-module **/
import { NotificationItem } from "@mail/core/public_web/notification_item";
import { patch } from "@web/core/utils/patch";
import { rpc } from "@web/core/network/rpc";
import { user } from "@web/core/user";

export async function ensureFavouriteChannelsLoaded(store) {
    if (!store) return [];
    if (!store.favouriteChannelIds) {
        store.favouriteChannelIds = [];
    }
    if (store._favouriteChannelsLoadedPromise) {
        return store._favouriteChannelsLoadedPromise;
    }
    store._favouriteChannelsLoadedPromise = (async () => {
        const userId = user.userId;
        if (userId) {
            try {
                const data = await rpc("/web/dataset/call_kw/res.users/search_read", {
                    model: "res.users",
                    method: "search_read",
                    args: [[["id", "=", userId]], ["mail_channel_ids"]],
                    kwargs: {},
                });
                const channelIds = data?.[0]?.mail_channel_ids || [];
                if (store.favouriteChannelIds) {
                    store.favouriteChannelIds.splice(0, store.favouriteChannelIds.length, ...channelIds);
                }
                for (const channelId of channelIds) {
                    const channel = store["discuss.channel"]?.get(channelId);
                    if (channel) {
                        channel.isFavourite = true;
                    }
                }
                return channelIds;
            } catch (e) {
                console.error("Failed to load favourite channels", e);
                store._favouriteChannelsLoadedPromise = null;
            }
        }
        return [];
    })();
    return store._favouriteChannelsLoadedPromise;
}

patch(NotificationItem.prototype, {
    setup() {
        super.setup(...arguments);
        if (this.store) {
            ensureFavouriteChannelsLoaded(this.store);
        }
    },
    getChannelId() {
        if (this.props?.channel?.id) {
            return this.props.channel.id;
        }
        const thread = this.props?.thread || this.props?.message?.thread;
        if (thread) {
            if (thread.model === "discuss.channel" && thread.id) {
                return thread.id;
            }
            if (thread.channel?.id) {
                return thread.channel.id;
            }
            if (typeof thread.id === "number") {
                return thread.id;
            }
        }
        return null;
    },
    isFavourite(channelId) {
        if (!channelId || !this.store) {
            return false;
        }
        const channel = this.store["discuss.channel"]?.get(channelId);
        if (channel && channel.isFavouriteChat !== undefined) {
            return Boolean(channel.isFavouriteChat);
        }
        return Boolean(this.store.favouriteChannelIds?.includes(channelId));
    },
    async toggleFavourite(channelId) {
        if (!channelId || !this.store) return;
        const favIds = this.store.favouriteChannelIds || [];
        const isFav = this.isFavourite(channelId);
        const userId = user.userId;
        const channel = this.store["discuss.channel"]?.get(channelId);

        if (isFav) {
            const index = favIds.indexOf(channelId);
            if (index > -1) {
                favIds.splice(index, 1);
            }
            if (channel) {
                channel.isFavourite = false;
                if (channel.self_member_id) {
                    channel.self_member_id.is_favorite = false;
                }
            }
            await rpc("/disable_favourite", {
                active_id: channelId,
            });
        } else {
            if (!favIds.includes(channelId)) {
                favIds.push(channelId);
            }
            if (channel) {
                channel.isFavourite = true;
                if (channel.self_member_id) {
                    channel.self_member_id.is_favorite = true;
                }
            }
            await rpc("/enable_favourite", {
                active_id: channelId,
            });
        }
    },
});
