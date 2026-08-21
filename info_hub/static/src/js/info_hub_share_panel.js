/** @odoo-module **/

import { Component, useState, onMounted, onWillUpdateProps } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";
import { user as currentUser } from "@web/core/user";
import { InvitePeopleDialog } from "./info_hub_invite_dialog";
import { _t } from "@web/core/l10n/translation";
import { ConfirmationDialog } from "@web/core/confirmation_dialog/confirmation_dialog";
import { router } from "@web/core/browser/router";

/**
 * OWL component that renders the sharing/permissions side panel for an article.
 *  *
 * Allows toggling website publication, changing article visibility, setting the
 * default access level, managing member permissions, and inviting new members.
 */
export class InfoSharePanel extends Component {
    static template = "info_hub.InfoSharePanel";
    static props = {
        article: { type: Object },
        onRefreshArticle: { type: Function },
        isSharedUser: { type: Boolean, optional: true },
    };

    setup() {
        this.orm = useService("orm");
        this.notification = useService("notification");
        this.dialog = useService("dialog");

        this.state = useState({
            websitePublished: this.props.article.website_published || false,
            visibility: this.props.article.visibility || 'everyone',
            defaultAccess: this.props.article.default_access || 'read',
            shareUrl: this.props.article.share_url || '',
            members: [],
            isWebsiteInstalled: false,
            loading: true,
        });

        onMounted(() => {
            this._loadData(this.props.article.id);
        });
    }

    onWillUpdateProps(nextProps) {
        const idChanged = nextProps.article.id !== this.props.article.id;
        const categoryChanged = nextProps.article.category !== this.props.article.category;

        if (idChanged || categoryChanged) {
            this.state.websitePublished = nextProps.article.website_published || false;
            this.state.visibility = nextProps.article.visibility || 'everyone';
            this.state.defaultAccess = nextProps.article.default_access || 'read';
            this.state.shareUrl = nextProps.article.share_url || '';
            this._loadData(nextProps.article.id);
        }
    }

    async _loadData(articleId) {
        this.state.loading = true;
        try {
            const isInstalled = await this.orm.call("info.hub.article", "check_website_installed", []);
            this.state.isWebsiteInstalled = isInstalled;

            await this._loadMembers(articleId);
        } catch (error) {
            console.error("Failed to load sharing details:", error);
        } finally {
            this.state.loading = false;
        }
    }

    async _loadMembers(articleId) {
        try {
            const members = await this.orm.searchRead(
                "info.hub.article.member",
                [["article_id", "=", articleId]],
                ["id", "partner_id", "permission", "member_type", "partner_email", "user_id"]
            );
            this.state.members = members;
        } catch (error) {
            console.error("Failed to load members list:", error);
        }
    }

     async onToggleShareToWeb() {
        const nextVal = !this.state.websitePublished;
        try {
            await this.orm.write("info.hub.article", [this.props.article.id], {
                website_published: nextVal,
            });
            this.state.websitePublished = nextVal;
            this.props.article.website_published = nextVal;

            const [art] = await this.orm.read("info.hub.article", [this.props.article.id], ["share_url"]);
            this.state.shareUrl = art.share_url || '';
            this.props.article.share_url = art.share_url || '';
        } catch {
            this.notification.add("Failed to toggle web sharing.", { type: "danger" });
        }
    }

    async onVisibilityChange(ev) {
        const val = ev.target.value;
        try {
            await this.orm.write("info.hub.article", [this.props.article.id], {
                visibility: val,
            });
            this.state.visibility = val;
            this.props.onRefreshArticle();
        } catch {
            this.notification.add("Failed to update visibility.", { type: "danger" });
        }
    }

    async onDefaultAccessChange(ev) {
        const val = ev.target.value;
        try {
            await this.orm.write("info.hub.article", [this.props.article.id], {
                default_access: val,
            });
            this.state.defaultAccess = val;
            this.props.article.default_access = val;
        } catch {
            this.notification.add("Failed to update default access rights.", { type: "danger" });
        }
    }

    async onMemberPermissionChange(memberId, ev) {
        const val = ev.target.value;
        try {
            await this.orm.write("info.hub.article.member", [memberId], {
                permission: val,
            });
            await this._loadMembers(this.props.article.id);
        } catch {
            this.notification.add("Failed to update member permission.", { type: "danger" });
        }
    }

    async onRemoveMember(memberId) {
        const member = this.state.members.find(m => m.id === memberId);
        const isSelf = member && member.user_id && member.user_id[0] === currentUser.userId;

        if (isSelf) {
            this.dialog.add(ConfirmationDialog, {
                title: _t("Leave Article"),
                body: _t("Are you sure you want to remove your member? By leaving an article, you may lose access to it."),
                confirmLabel: _t("Leave"),
                confirm: async () => {
                    await this._executeRemoveMember(memberId, true);
                },
                cancel: () => {},
            });
        } else {
            await this._executeRemoveMember(memberId, false);
        }
    }

    async _executeRemoveMember(memberId, isSelf) {
        try {
            await this.orm.unlink("info.hub.article.member", [memberId]);

            if (isSelf) {
                router.pushState({ resId: undefined, article_id: undefined });
                window.location.reload();
            } else {
                await this._loadMembers(this.props.article.id);
                this.props.onRefreshArticle();
            }
        } catch {
            this.notification.add(_t("Failed to remove member."), { type: "danger" });
        }
    }

    onCopyUrl() {
        if (!this.state.shareUrl) return;
        navigator.clipboard.writeText(this.state.shareUrl);
    }

    onInviteClick() {
        this.dialog.add(InvitePeopleDialog, {
            article: this.props.article,
            onInviteSent: async () => {
                await this._loadMembers(this.props.article.id);
                this.props.onRefreshArticle();
            }
        });
    }

    isOwner(member) {

        if (!member.user_id || !this.props.article.author_id) return false;
        return member.user_id[0] === this.props.article.author_id[0];
    }

    get currentUserId() {
        return currentUser.userId;
    }
}
