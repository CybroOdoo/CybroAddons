/** @odoo-module **/
import {
    MENU_TABS,
    MessagingMenu,
} from "@mail/core/public_web/messaging_menu/messaging_menu_model";
import { MessagingMenu as MessagingMenuComponent } from "@mail/core/public_web/messaging_menu/messaging_menu";
import { MessagingMenuTab } from "@mail/core/public_web/messaging_menu/messaging_menu_tab_model";
import { DiscussChannel } from "@mail/discuss/core/common/discuss_channel_model";
import { Store } from "@mail/core/common/store_service";
import { fields } from "@mail/model/export";
import { _t } from "@web/core/l10n/translation";
import { patch } from "@web/core/utils/patch";
import { ensureFavouriteChannelsLoaded } from "./notification_item";

MENU_TABS.FAVOURITE = "favourite";

patch(Store.prototype, {
    setup() {
        super.setup(...arguments);
        this.favouriteChannelIds = fields.Attr([], { asProxy: true });
    },
});

patch(DiscussChannel.prototype, {
    setup() {
        super.setup(...arguments);
        this.isFavouriteChat = this.computed(() => {
            return Boolean(
                this.isFavourite ||
                this.store.favouriteChannelIds?.includes(this.id) ||
                this.self_member_id?.is_favorite
            );
        });
        this.isFavourite = fields.Attr(false);
    },
});

patch(MessagingMenuTab.prototype, {
    _computeCounter() {
        if (this.id === MENU_TABS.FAVOURITE) {
            return this.store.favouriteChannelIds?.length ?? 0;
        }
        return super._computeCounter(...arguments);
    },
});

patch(MessagingMenu.prototype, {
    setup() {
        super.setup(...arguments);
        this.favouriteTab = fields.One("MessagingMenuTab", {
            compute() {
                return {
                    id: MENU_TABS.FAVOURITE,
                    recordType: "discuss.channel",
                    includesChannel: (c) => Boolean(c.isFavouriteChat),
                    icon: "star",
                    activeIcon: "star",
                    sequence: 50,
                    label: _t("Favourites"),
                    emptyState: {
                        title: _t("No favourite chats found"),
                        subtitle: _t("Star conversations to quickly access them here."),
                    },
                    filters: [
                        {
                            id: "favourite_unread",
                            text: _t("Unread"),
                            includesChannel: (c) => c.isUnread,
                        },
                    ],
                };
            },
            eager: true,
        });
    },
});

patch(MessagingMenuComponent.prototype, {
    setup() {
        super.setup(...arguments);
        ensureFavouriteChannelsLoaded(this.store);
    },
});
