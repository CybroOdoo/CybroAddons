/** @odoo-module **/

import { Component, useState, onMounted } from "@odoo/owl";
import { Dialog } from "@web/core/dialog/dialog";
import { useService } from "@web/core/utils/hooks";

/**
 * Dialog for searching and selecting a info article (used for "Move to" and link-insertion flows).
 */
export class ArticleSearchDialog extends Component {
    static template = "info_hub.ArticleSearchDialog";
    static components = { Dialog };
    static props = {
        close: { type: Function },
        onArticleSelected: { type: Function },
    };

    setup() {
        this.orm = useService("orm");
        this.state = useState({
            articles: [],
            searchQuery: "",
            loading: true,
        });

        onMounted(() => {
            this._loadArticles();
        });
    }

    async _loadArticles() {
        try {
            this.state.loading = true;
            const articles = await this.orm.searchRead(
                "info.hub.article",
                [["active", "=", true]],
                ["id", "name", "icon"],
                { limit: 50, order: "name asc" }
            );
            this.state.articles = articles;
        } catch (error) {
            console.error("Failed to load articles:", error);
        } finally {
            this.state.loading = false;
        }
    }

    get filteredArticles() {
        const query = this.state.searchQuery.toLowerCase().trim();
        if (!query) {
            return this.state.articles;
        }
        return this.state.articles.filter((a) => a.name.toLowerCase().includes(query));
    }

    onSearchInput(ev) {
        this.state.searchQuery = ev.target.value;
    }

    selectArticle(article) {
        this.props.onArticleSelected(article);
        this.props.close();
    }
}
