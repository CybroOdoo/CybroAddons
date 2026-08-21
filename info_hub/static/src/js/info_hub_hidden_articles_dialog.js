/** @odoo-module **/

import { Component, useState, onMounted, useRef } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";

/**
 * Dialog that lists workspace and shared articles the current user has not yet joined.
 *  *
 * Provides a debounced search input and a "Join" button per article. Joining adds the
 * user as a member with the article's default access level and refreshes the sidebar.
 */
export class InfoHiddenArticlesDialog extends Component {
    static template = "info_hub.InfoHiddenArticlesDialog";

    static props = {

        onJoined: { type: Function, optional: true },

        onClose: { type: Function, optional: true },
    };

    setup() {
        this.orm = useService("orm");
        this.notification = useService("notification");

        this.state = useState({
            searchTerm: "",
            articles: [],
            loading: true,
            joiningId: null,
        });

        this.searchInputRef = useRef("searchInput");

        onMounted(async () => {
            await this._loadHiddenArticles();
            if (this.searchInputRef.el) {
                this.searchInputRef.el.focus();
            }
        });
    }

    async _loadHiddenArticles(searchTerm = "") {
        this.state.loading = true;
        try {
            const articles = await this.orm.call(
                "info.hub.article",
                "get_hidden_workspace_articles",
                [],
                { search_term: searchTerm }
            );
            this.state.articles = articles;
        } catch {
            this.notification.add("Failed to load hidden articles.", { type: "danger" });
            this.state.articles = [];
        } finally {
            this.state.loading = false;
        }
    }

    onSearchInput(ev) {
        const value = ev.target.value;
        this.state.searchTerm = value;

        clearTimeout(this._searchDebounce);
        this._searchDebounce = setTimeout(() => {
            this._loadHiddenArticles(value.trim());
        }, 250);
    }

    async joinArticle(article) {
        if (this.state.joiningId) return;
        this.state.joiningId = article.id;
        try {
            const result = await this.orm.call(
                "info.hub.article",
                "action_join_article",
                [[article.id]]
            );
            if (result) {

                this.state.articles = this.state.articles.filter(
                    (a) => a.id !== article.id
                );
                if (this.props.onJoined) {
                    this.props.onJoined(article.id);
                }
            }
        } catch {
            this.notification.add("Failed to join article.", { type: "danger" });
        } finally {
            this.state.joiningId = null;
        }
    }

    close() {
        if (this.props.onClose) {
            this.props.onClose();
        }
    }

    onDialogClick(ev) {
        ev.stopPropagation();
    }

    getAccessLabel(article) {
        if (article.default_access === "edit") return "Can Edit";
        return "Can Read";
    }
}
