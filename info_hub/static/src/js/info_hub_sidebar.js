/** @odoo-module **/

import { Component, useState } from "@odoo/owl";

/**
 * OWL component that renders the left-side navigation sidebar.
 *  *
 * Displays workspace, shared, private, and favourited articles as a collapsible
 * tree. Delegates article selection and new-article creation to the parent
 * InfoApp component via env methods.
 */
export class InfoSidebar extends Component {
    static template = "info_hub.InfoSidebar";

    setup() {
        this.state = useState({
            isSearchExpanded: false
        });
    }

    toggleSearch(expanded) {
        this.state.isSearchExpanded = expanded;
        if (expanded) {
            setTimeout(() => {
                const input = document.querySelector(".o_info_hub_sidebar_search");
                if (input) input.focus();
            }, 50);
        } else {
            this.props.onFilterInput({ target: { value: "" } });
        }
    }
    static props = {
        articles: { type: Array },
        activeArticleId: { optional: true },
        filterText: { type: String },
        expandedArticles: { type: Object },
        isSharedUser: { type: Boolean, optional: true },
        onSelectArticle: { type: Function },
        onFilterInput: { type: Function },
        onNewArticle: { type: Function },
        onNewArticleInSection: { type: Function },
        onNewSubArticle: { type: Function },
        toggleArticleExpand: { type: Function },
        onDragStart: { type: Function },
        onDragEnd: { type: Function },
        onDragOver: { type: Function },
        onDragLeave: { type: Function },
        onDrop: { type: Function },
        onBrowseTemplates: { type: Function },
        openTrash: { type: Function },
        onSearchHiddenArticles: { type: Function },
        toggleSidebar: { type: Function },
    };

    getFilteredArticles(category) {
        const filter = this.props.filterText.toLowerCase();
        return this.props.articles.filter((a) => {
            if (a.is_article_item) return false;
            if (a.category !== category) return false;
            if (filter) {
                return a.name.toLowerCase().includes(filter);
            }
            return !a.parent_id;
        });
    }

    getChildArticles(parentId) {
        if (this.props.filterText) return [];
        return this.props.articles.filter((a) => {
            if (a.is_article_item) return false;
            const pid = Array.isArray(a.parent_id) ? a.parent_id[0] : a.parent_id;
            return pid === parentId;
        });
    }

    getFavoritedArticles() {
        const filter = this.props.filterText.toLowerCase();
        return this.props.articles.filter((a) => {
            if (a.is_article_item) return false;
            return a.is_favorite && (!filter || a.name.toLowerCase().includes(filter));
        });
    }

    getArticleTree(category) {
        const filter = this.props.filterText.toLowerCase();
        const sectionArticles = this.props.articles.filter((a) => {
            if (a.is_article_item) return false;
            return a.category === category;
        });

        if (filter) {
            return sectionArticles.filter(a => a.name.toLowerCase().includes(filter)).map(a => ({
                ...a,
                level: 0,
                hasChildren: false,
                isExpanded: false
            }));
        }

        const childrenMap = {};
        sectionArticles.forEach((art) => {
            const pId = art.parent_id ? art.parent_id[0] : null;
            if (!childrenMap[pId]) {
                childrenMap[pId] = [];
            }
            childrenMap[pId].push(art);
        });

        const articleIds = new Set(sectionArticles.map(a => a.id));
        const roots = sectionArticles.filter((art) => {
            const pId = art.parent_id ? art.parent_id[0] : null;
            return !pId || !articleIds.has(pId);
        });

        const result = [];
        const traverse = (art, level) => {
            const children = childrenMap[art.id] || [];
            const isExpanded = this.props.expandedArticles[art.id] !== false;
            result.push({
                ...art,
                level: level,
                hasChildren: children.length > 0,
                isExpanded: isExpanded
            });

            if (isExpanded) {
                children.forEach((child) => {
                    traverse(child, level + 1);
                });
            }
        };

        roots.forEach((root) => traverse(root, 0));
        return result;
    }
}
