/**
 * WhatsApp Chat Layout - Sidebar Patch for Odoo 20 (Owl 3)
 * Patches MessagingMenu (the Odoo 20 left sidebar in Discuss) to add:
 *  - User avatar at the top
 *  - 4-tab WhatsApp icon bar: Mail / Chats / Channels / Video Calls
 */
import { patch } from "@web/core/utils/patch";
import { MessagingMenu } from "@mail/core/public_web/messaging_menu/messaging_menu";
import {
    MENU_TABS,
    MessagingMenu as MessagingMenuModel,
} from "@mail/core/public_web/messaging_menu/messaging_menu_model";
import { fields } from "@mail/model/export";
import { _t } from "@web/core/l10n/translation";
import { onMounted, onWillStart, signal } from "@odoo/owl";
import { rpc } from "@web/core/network/rpc";

/**
 * Patch the MessagingMenu data model so that notificationTab is always
 * computed and available for any user, regardless of their user profile
 * notification setting (email vs inbox).
 */
patch(MessagingMenuModel.prototype, {
    setup() {
        super.setup(...arguments);
        this.notificationTab = fields.One("MessagingMenuTab", {
            compute() {
                return {
                    id: MENU_TABS.NOTIFICATION,
                    recordType: "mail.message",
                    includesMessage: (msg) =>
                        (msg.needaction || msg.needaction_done) && this.notificationMatchesExtra(msg),
                    icon: "notifications",
                    activeIcon: "notifications",
                    sequence: 60,
                    label: _t("Notifications"),
                    emptyState: {
                        title: _t("You're all caught up!"),
                        subtitle: _t("Notifications of the documents you follow will appear here."),
                    },
                    filters: [
                        {
                            id: "notification_unread",
                            text: _t("Unread"),
                            includesMessage: (msg) =>
                                msg.needaction && this.notificationMatchesExtra(msg),
                            isDefault: true,
                        },
                    ],
                    actions: [
                        {
                            id: "mark-all-read",
                            text: _t("Mark all read"),
                            isDisabled: () => !this.notificationTab?.counter,
                            onClick: () => this.store.markNeedactionMessagesAsRead(),
                            preventDropdownClose: true,
                        },
                    ],
                };
            },
            eager: true,
        });
    },
});

/**
 * Patch the MessagingMenu Owl component to display the avatar and 4-tab bar.
 */
patch(MessagingMenu.prototype, {
    setup() {
        super.setup(...arguments);
        this.waUserAvatar = signal(null);

        onWillStart(async () => {
            try {
                const result = await rpc("/select_color", {});
                if (result) {
                    const root = document.documentElement;
                    if (result.background_color) {
                        root.style.setProperty("--background-color", result.background_color);
                    }
                    if (result.layout_color) {
                        root.style.setProperty("--layout-color", result.layout_color);
                    }
                }
            } catch (e) {
                // Silently ignore color-fetch errors
            }
        });

        onMounted(() => {
            this._waFetchUserAvatar();
        });
    },

    get waAvatarSrc() {
        const avatar = this.waUserAvatar();
        if (avatar && typeof avatar === "string" && !avatar.startsWith("BinaryValue") && !avatar.startsWith("<")) {
            return `data:image/png;base64,${avatar}`;
        }
        return this.store?.self?.avatarUrl || "/web/static/img/placeholder.png";
    },

    get isMailTabActive() {
        const id = this.activeTab?.()?.id;
        return id === "notification" || id === "bookmark";
    },

    async _waFetchUserAvatar() {
        try {
            const result = await rpc("/select_user_image", {});
            if (result) {
                this.waUserAvatar.set(result);
            }
        } catch (e) {
            // ignore
        }
    },

    _onWaSelectTab(tabId) {
        if (tabId === "meeting") {
            const meetingTab =
                this.visibleTabs?.find((t) => t.id === "meeting") ||
                this.store?.messagingMenu?.allTabs?.find((t) => t.id === "meeting");
            if (meetingTab) {
                this.state().selectTab(meetingTab);
                return;
            }
            if (this.store && typeof this.store.requestStartMeeting === "function") {
                this.store.requestStartMeeting();
                return;
            }
        }

        if (tabId === "notification" || tabId === "mail") {
            const notifTab =
                this.visibleTabs?.find((t) => t.id === "notification") ||
                this.store?.messagingMenu?.allTabs?.find((t) => t.id === "notification") ||
                this.store?.messagingMenu?.notificationTab;
            if (notifTab) {
                this.state().selectTab(notifTab);
                return;
            }
            const bookmarkTab =
                this.visibleTabs?.find((t) => t.id === "bookmark") ||
                this.store?.messagingMenu?.allTabs?.find((t) => t.id === "bookmark") ||
                this.store?.messagingMenu?.bookmarkTab;
            if (bookmarkTab) {
                this.state().selectTab(bookmarkTab);
                return;
            }
            const unreadFilter = this.activeTab?.()?.filters?.find((f) => f.id?.includes("unread"));
            if (unreadFilter) {
                this.state().selectedFilter =
                    this.state().selectedFilter?.id === unreadFilter.id ? undefined : unreadFilter;
            }
            return;
        }

        const targetTab =
            this.visibleTabs?.find((t) => t.id === tabId) ||
            this.store?.messagingMenu?.allTabs?.find((t) => t.id === tabId);
        if (targetTab) {
            this.state().selectTab(targetTab);
        }
    },
});
