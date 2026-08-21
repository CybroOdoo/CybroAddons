/** @odoo-module **/

import { Component, useState, onMounted, onWillUnmount, onWillStart, onWillUpdateProps, markup, useRef, useSubEnv, onPatched } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { Wysiwyg } from "@html_editor/wysiwyg";
import { HtmlViewer } from "@html_editor/components/html_viewer/html_viewer";
import { MAIN_PLUGINS, EMBEDDED_COMPONENT_PLUGINS } from "@html_editor/plugin_sets";
import { MAIN_EMBEDDINGS } from "@html_editor/others/embedded_components/embedding_sets";
import { Plugin } from "@html_editor/plugin";
import { router, routerBus } from "@web/core/browser/router";
import { BrowseTemplatesDialog, InsertKanbanViewDialog, InsertListViewDialog, InsertCalendarViewDialog, InfoArticleVersionHistoryDialog } from "./info_hub_templates_dialog";
import { Chatter } from "@mail/chatter/web_portal/chatter";
import { InfoSidebar } from "./info_hub_sidebar";
import { View, getDefaultConfig } from "@web/views/view";
import { ListController } from "@web/views/list/list_controller";
import { listView } from "@web/views/list/list_view";
import { calendarView } from "@web/views/calendar/calendar_view";
import { CalendarController } from "@web/views/calendar/calendar_controller";
import { Dropdown } from "@web/core/dropdown/dropdown";
import { DropdownItem } from "@web/core/dropdown/dropdown_item";
import { _t } from "@web/core/l10n/translation";
import { isHtmlContentSupported } from "@html_editor/core/selection_plugin";
import { kanbanEmbedding } from "./embedded_kanban";
import { infoCardEmbedding } from "./embedded_card_view";
import { renderToElement } from "@web/core/utils/render";
import { InfoSharePanel } from "./info_hub_share_panel";
import { InfoHiddenArticlesDialog } from "./info_hub_hidden_articles_dialog";
import { FoldableSectionPlugin } from "./foldable_section_plugin";
import { ClipboardPluginCommunity } from "./clipboard_plugin";
import { ArticlePluginCommunity } from "./article_plugin";
import { ConfirmationDialog } from "@web/core/confirmation_dialog/confirmation_dialog";
import { InfoCoverDialog } from "./info_hub_cover_dialog";
import { TableOfContentManager } from "@html_editor/others/embedded_components/core/table_of_content/table_of_content_manager";
import { EmbeddedTableOfContentComponent } from "@html_editor/others/embedded_components/core/table_of_content/table_of_content";
import { user } from "@web/core/user";

/**
 * OWL Plugin that registers the "Insert Kanban" powerbox command.
 * Creates an embedded kanban view of article items when the command is triggered.
 */
export class KanbanPlugin extends Plugin {
    static id = "kanban";
    static dependencies = ["history", "dom", "selection", "dialog"];
    resources = {
        user_commands: [
            {
                id: "insert_kanban",
                title: "Item Kanban",
                description: "Insert a Kanban view of article items",
                icon: "fa-th-large",
                run: () => {
                    const resId = this.config.getRecordInfo?.()?.resId;
                    if (!resId) return;
                    let cursor = this.dependencies.selection.preserveSelection();
                    this.services.dialog.add(
                        InsertKanbanViewDialog,
                        {
                            onInsert: async (name) => {
                                cursor = null;
                                try {
                                    await this.services.orm.call(
                                        "info.hub.article",
                                        "create_default_item_stages",
                                        [resId]
                                    );
                                } catch {  }
                                this._insertBlock(resId, name);
                                window.dispatchEvent(new Event("info-set-full-width"));
                            },
                        },
                        { onClose: () => cursor?.restore() }
                    );
                },
            }
        ],
        powerbox_items: [
            {
                commandId: "insert_kanban",
                categoryId: "structure",
            }
        ]
    };

    _insertBlock(resId, displayName = "Items") {
        const embeddedProps = JSON.stringify({ viewProps: { resId, displayName } });
        const block = renderToElement("info_hub.EmbeddedKanbanBlueprint", { embeddedProps });
        this.dependencies.dom.insert(block);
        this.dependencies.history.addStep();
    }
}

/**
 * Root OWL component for the Information module.
 *  *
 * Renders a two-column layout:
 *   - Left: collapsible sidebar with workspace/article tree
 *   - Right: article reader/editor pane (welcome screen or article body)
 *  *
 * Registered as a client action so it is mounted when the Information menu item is clicked.
 */
export class InfoApp extends Component {
    static template = "info_hub.InfoApp";
    static components = { Wysiwyg, HtmlViewer, Chatter, InfoSidebar, View, InfoSharePanel, InfoHiddenArticlesDialog, EmbeddedTableOfContentComponent };

    setup() {
        this.orm = useService("orm");
        this.notification = useService("notification");
        this.action = useService("action");
        this.dialog = useService("dialog");

        this.newArticleCreated = false;
        this.bodyEditorRef = useRef("bodyEditor");
        this.editorContainerRef = useRef("editorContainer");

        this.hasCurrencyField = false;
        this.orm.call("info.hub.article", "fields_get", [["currency_id"]]).then(fields => {
            if (fields && fields.currency_id) {
                this.hasCurrencyField = true;
            }
        }).catch(() => {});

        this._drag = {
            articleId: null,
            sourceSection: null,
            overEl: null,
            startX: null,
            currentX: null,
        };
        // Property drag-and-drop state
        this._propDrag = {
            sourceIndex: null,
        };

        this._editorMountCount = 0;

        this.state = useState({
            loading: true,
            isSidebarOpen: true,
            workspaces: [],
            articles: [],
            activeArticleId: null,
            activeArticle: null,
            articleLoading: false,
            filterText: "",
            showChatter: false,
            showTOCPanel: false,
            hasHeadings: false,
            favorited: false,
            editorDirty: false,
            editorKey: 0,
            history: [],
            historyIndex: -1,
            isLocked: false,
            isFullWidth: false,
            showCoverUpload: false,
            showEmojiPicker: false,
            emojiSearchQuery: "",
            emojiActiveCategory: "smileys",
            coverObjectPosition: 50,
            showMoveToDialog: false,
            moveToArticleId: null,
            showVersionHistory: false,
            versionHistory: [],
            expandedArticles: {},
            showAddPropertyPopup: false,
            showPropertiesPanel: false,
            customProperties: [],
            newPropertyLabel: "Property 1",
            newPropertyType: "Text",
            showFieldTypeDropdown: false,
            editingPropertyIndex: null,
            newPropertySelectionValues: [],
            newPropertyTags: [],
            tagsFocused: false,
            newPropertyModel: "",
            showModelDropdown: false,
            availableModels: [],
            domainRules: [],
            domainMatchType: "all",
            domainIncludeArchived: false,
            domainRecordCount: null,
            showEditorHelper: false,
            kanbanStages: [],
            kanbanViewId: false,
            archivedKanbanItems: [],
            showSlashMenu: false,
            slashMenuStyle: "",
            slashMenuRange: null,
            isSharedUser: false,
            sharedArticles: [],
            privateArticles: [],
            favoritedArticles: [],
            pendingReadingId: null,
            activeM2oPropIndex: null,
            m2oRecords: [],
            m2oSearchQuery: "",
            showSignaturePopup: false,
            activeSignaturePropIndex: null,
            sigTab: "draw",
            sigLoadedImage: null,
            newSeparatorState: "open",
            newPropertySuffix: "",
            newPropertyDisplayInCards: false,
            newPropertyDefaultValue: "",
            newPropertyDefaultValueId: null,
            showPopupDefaultValueDropdown: false,
            popupDefaultValueRecords: [],
            parentPropertyMap: {},
            articlePropertyValues: {},
            tagCreationQuery: "",
            htmlPopupEditorKey: 0,
            repositioning: false,
            coverDragStartY: null,
        });

        const self = this;
        this.tocManager = new TableOfContentManager({
            get el() {
                return self.getArticleBodyEl();
            }
        });

        const originalUpdateStructure = this.tocManager.updateStructure.bind(this.tocManager);
        this.tocManager.updateStructure = () => {
            originalUpdateStructure();
            if (this.tocManager.structure && this.tocManager.structure.headings) {
                this.tocManager.structure.headings = this.tocManager.structure.headings.filter(h => {
                    const text = h.name ? h.name.trim().toLowerCase() : "";
                    return text.replaceAll("\u200B", "").length > 0 && text !== "untitled" && text !== "untitled article";
                });
            }
        };

        this.onRouteChange = this.onRouteChange.bind(this);
        this.onSelectArticleEvent = this.onSelectArticleEvent.bind(this);
        this.onSetFullWidthEvent = this.onSetFullWidthEvent.bind(this);

        this._htmlPopupEditor = null;
        this._htmlValueEditors = {};

        this.lastScrolledArticleId = null;

        onMounted(() => {
            this._loadData();
            routerBus.addEventListener("ROUTE_CHANGE", this.onRouteChange);
            window.addEventListener("select-article", this.onSelectArticleEvent);
            window.addEventListener("info-set-full-width", this.onSetFullWidthEvent);
            this._checkScrollToTop();
        });

        onPatched(() => {
            this._checkScrollToTop();
        });

        onWillUnmount(() => {
            routerBus.removeEventListener("ROUTE_CHANGE", this.onRouteChange);
            window.removeEventListener("select-article", this.onSelectArticleEvent);
            window.removeEventListener("info-set-full-width", this.onSetFullWidthEvent);
            if (this._onWindowMouseMove) {
                window.removeEventListener("mousemove", this._onWindowMouseMove);
            }
            if (this._onWindowMouseUp) {
                window.removeEventListener("mouseup", this._onWindowMouseUp);
            }
        });
    }

    onSelectArticleEvent(ev) {
        if (ev.detail && ev.detail.articleId) {
            this.selectArticle(ev.detail.articleId);
        }
    }

    async onSetFullWidthEvent() {
        if (!this.state.activeArticleId || this.state.isFullWidth) return;
        try {
            await this.orm.write("info.hub.article", [this.state.activeArticleId], {
                is_full_width: true,
            });
            this.state.isFullWidth = true;
        } catch (e) {
            console.error("Failed to set full width automatically:", e);
        }
    }

    async onRefreshSharePanel() {
        await this._loadData(true);
        if (this.state.activeArticleId) {
            await this.selectArticle(this.state.activeArticleId, false, true);
        }
    }
     async _loadData(skipAutoSelect = false, goToHome = false) {
        try {
            if (!this.state.kanbanViewId) {
                this.state.kanbanViewId = await this.orm.call(
                    "info.hub.article",
                    "get_kanban_view_id",
                    []
                );
            }

            const meta = await this.orm.call("info.hub.article", "get_user_metadata", []);
            this.state.isSharedUser = meta.is_shared_user;

            this.orm.searchRead("ir.model", [], ["name", "model"]).then(models => {
                const sorted = models.filter(m => m.name).sort((a, b) => a.name.localeCompare(b.name));
                this.state.availableModels = [...new Set(sorted.map(m => m.name))];
                const details = {};
                sorted.forEach(m => { details[m.name] = m.model; });
                this.state.availableModelDetails = details;
            }).catch(() => {
                this.state.availableModels = [];
                this.state.availableModelDetails = {};
            });

            let articles = [];
            if (this.state.isSharedUser) {
                const data = await this.orm.call("info.hub.article", "get_shared_sidebar_data", []);
                this.state.sharedArticles = data.articles;
                this.state.privateArticles = data.private;
                this.state.favoritedArticles = data.favorites;
                articles = [...data.articles, ...data.private];
            } else {
                articles = await this.orm.call(
                    "info.hub.article",
                    "get_sidebar_articles",
                    []
                );
            }

            this.state.workspaces = [];
            this.state.articles = articles;

            // Skip auto-selection when refreshing data (e.g. after restore/archive)
            if (skipAutoSelect) return;

            let targetArticleId = null;
            if (goToHome) {
                if (this.props.resId) this.props.resId = null;
                if (this.props.action) {
                    if (this.props.action.res_id) this.props.action.res_id = null;
                    if (this.props.action.params) {
                        this.props.action.params.article_id = null;
                        this.props.action.params.id = null;
                    }
                    if (this.props.action.context) this.props.action.context.active_id = null;
                }
                router.current.article_id = undefined;
                router.current.active_id = undefined;
                router.current.id = undefined;
                router.pushState({ article_id: undefined, active_id: undefined, id: undefined }, { replaceState: true });
            } else {
                if (router.current.article_id) {
                    targetArticleId = Number(router.current.article_id);
                } else if (router.current.active_id) {
                    targetArticleId = Number(router.current.active_id);
                } else if (router.current.id) {
                    targetArticleId = Number(router.current.id);
                } else if (this.props.resId) {
                    targetArticleId = Number(this.props.resId);
                } else if (this.props.action?.res_id) {
                    targetArticleId = Number(this.props.action.res_id);
                } else if (this.props.action?.params?.article_id) {
                    targetArticleId = Number(this.props.action.params.article_id);
                } else if (this.props.action?.context?.active_id) {
                    targetArticleId = Number(this.props.action.context.active_id);
                } else {
                    // Prioritize the first favorite article on general module open
                    const favoriteArticles = articles.filter((a) => a.is_favorite && !a.is_article_item);
                    if (favoriteArticles.length > 0) {
                        targetArticleId = favoriteArticles[0].id;
                    }
                }
            }

            if (this.props.action?.context?.new_article_created) {
                this.newArticleCreated = true;
            }

            if (!targetArticleId) {
                const favoriteArticles = articles.filter((a) => a.is_favorite);
                if (favoriteArticles.length > 0) {
                    targetArticleId = favoriteArticles[0].id;
                }
            }

            if (targetArticleId) {
                router.pushState({ article_id: targetArticleId, active_id: targetArticleId, id: targetArticleId }, { replaceState: true });
                // Always try to load the article directly.
                // Trashed (inactive) articles won't be in the sidebar list but
                // can still be fetched by selectArticle, which will show the
                // appropriate trash banner.
                await this.selectArticle(targetArticleId);
            }
        } catch (err) {
            console.error("Failed to load data in InfoApp:", err);
            this.notification.add("Failed to load data.", { type: "danger" });
        } finally {
            this.state.loading = false;
        }
    }

    async onRouteChange() {
        const urlArticleId = router.current.article_id ? Number(router.current.article_id) :
                             (router.current.active_id ? Number(router.current.active_id) :
                             (router.current.id ? Number(router.current.id) : null));
        if (urlArticleId) {
            if (this.state.activeArticleId !== urlArticleId) {
                // Always attempt to load — trashed articles won't be in
                // state.articles but selectArticle can still fetch them.
                await this.selectArticle(urlArticleId, false);
            }
        } else {
            this.state.activeArticleId = null;
            this.state.activeArticle = null;
        }
    }

    getFilteredArticles(workspaceType) {
        const filter = this.state.filterText.toLowerCase();
        return this.state.articles.filter((a) => {
            const ws = this.state.workspaces.find((w) => w.id === a.workspace_id[0]);
            if (!ws || ws.workspace_type !== workspaceType) return false;
            if (a.is_article_item) return false;
            if (filter) {
                return a.name.toLowerCase().includes(filter);
            }
            return !a.parent_id;
        });
    }

    getChildArticles(parentId) {
        if (this.state.filterText) return [];
        return this.state.articles.filter((a) => {
            const pid = Array.isArray(a.parent_id) ? a.parent_id[0] : a.parent_id;
            return pid === parentId && !a.is_article_item;
        });
    }

    hasChildArticles(articleId) {
        return this.state.articles.some((a) => {
            const pid = Array.isArray(a.parent_id) ? a.parent_id[0] : a.parent_id;
            return pid === articleId && !a.is_article_item;
        });
    }

    toggleArticleExpand(articleId, ev) {
        ev.stopPropagation();
        if (this.state.expandedArticles[articleId] === undefined) {
            this.state.expandedArticles[articleId] = false;
        } else {
            this.state.expandedArticles[articleId] = !this.state.expandedArticles[articleId];
        }
    }

    async onNewSubArticle(parentId, ev) {
        if (ev && ev.stopPropagation) ev.stopPropagation();
        try {
            const parentArt = this.state.articles.find((a) => a.id === parentId);
            if (!parentArt) return;

            const res = await this.orm.create("info.hub.article", [{
                name: "Untitled",
                category: parentArt.category,
                parent_id: parentId,
                body: "",
            }]);
            const newId = Array.isArray(res) ? res[0] : res;

            this.state.expandedArticles[parentId] = true;

            this.newArticleCreated = true;
            await this._loadData(true);
            await this.selectArticle(newId);
        } catch {
            this.notification.add("Could not create sub-article.", { type: "danger" });
        }
    }

    async selectArticle(articleId, updateHistory = true, forceReload = false) {
        if (!forceReload && this.state.activeArticleId === articleId) return;

        if (this.state.editorDirty && this.state.activeArticleId) {
            await this.saveChanges();
        }

        this._saveCurrentArticlePropertyValues();

        this.state.activeArticleId = articleId;
        this.state.activeArticle = null;
        this.state.articleLoading = true;
        this.state.editorDirty = false;
        this.state.editorKey = 0;

        try {
            const [record] = await this.orm.read(
                "info.hub.article",
                [articleId],
                ["id", "name", "icon", "body", "author_id", "last_edition_uid", "last_edition_date", "category", "cover_image", "parent_id", "is_favorite", "display_mode", "stage_id", "website_published", "share_url", "visibility", "default_access", "user_permission", "is_article_item", "is_template", "active"],
                { context: { active_test: false } }
            );
            if (this.props.resId !== undefined) {
                this.props.resId = articleId;
            }
            if (this.props.action) {
                this.props.action.res_id = articleId;
                if (!this.props.action.params) {
                    this.props.action.params = {};
                }
                this.props.action.params.article_id = articleId;
                this.props.action.params.id = articleId;
                if (!this.props.action.context) {
                    this.props.action.context = {};
                }
                this.props.action.context.active_id = articleId;
            }
            this.state.activeArticle = record;
            this.state.activeArticle.bodyMarkup = record.body ? markup(record.body) : "";
            this.state.coverObjectPosition = record.cover_image_position !== undefined ? record.cover_image_position : 50;
            this.state.favorited = !!record.is_favorite;

            const pendingReading = await this.orm.searchRead(
                "info.hub.article.reading",
                [["article_id", "=", articleId], ["user_id", "=", user.userId], ["state", "=", "pending"]],
                ["id"]
            );
            this.state.pendingReadingId = pendingReading.length > 0 ? pendingReading[0].id : null;
            this.state.showVersionHistory = false;
            this.state.showMoveToDialog = false;
            this.state.showCoverUpload = false;
            this.state.repositioning = false;
            this.state.coverDragStartY = null;

            const newParentId = record.parent_id
                ? (Array.isArray(record.parent_id) ? record.parent_id[0] : record.parent_id)
                : null;
            this._loadPropertiesForArticle(articleId, newParentId);

            const bodyEmpty = !record.body || record.body.trim() === "" || record.body.trim() === "<p><br></p>" || record.body.trim() === "<p><br/></p>";
            this.state.showEditorHelper = bodyEmpty && !!this.newArticleCreated;
            this.newArticleCreated = false;

            if (record.display_mode === "kanban") {
                await this._loadKanbanStages(articleId);
                if (!record.active) {
                    await this._loadArchivedKanbanItems(articleId);
                } else {
                    this.state.archivedKanbanItems = [];
                }
            } else {
                this.state.kanbanStages = [];
            }

            try {
                const [extra] = await this.orm.read(
                    "info.hub.article",
                    [articleId],
                    ["is_locked", "is_full_width"],
                    { context: { active_test: false } }
                );
                this.state.isLocked = !!extra.is_locked;
                this.state.isFullWidth = !!extra.is_full_width;
            } catch {
                this.state.isLocked = false;
                this.state.isFullWidth = false;
            }

            const parentId = record.parent_id ? (Array.isArray(record.parent_id) ? record.parent_id[0] : record.parent_id) : null;
            await this._loadPropertiesForArticle(articleId, parentId);

            this._originalName = record.name;
            this._originalBody = record.body || "";
            this._originalParentPropertyDefs = parentId ? JSON.parse(JSON.stringify(this.state.parentPropertyMap[parentId] || [])) : [];
            this._originalArticlePropertyValues = JSON.parse(JSON.stringify(this.state.articlePropertyValues[articleId] || {}));

            if (updateHistory) {
                router.pushState({ article_id: articleId, active_id: articleId, id: articleId });
                this.state.history = this.state.history.slice(0, this.state.historyIndex + 1);
                this.state.history.push(articleId);
                this.state.historyIndex = this.state.history.length - 1;
            }
        } catch {
            this.notification.add("Could not load article.", { type: "danger" });
        } finally {
            this.state.articleLoading = false;
            this._detectHeadingsFromBody(this.state.activeArticle?.body);
            setTimeout(() => {
                this.updateTOCState();
                if (this.editorContainerRef.el) {
                    this.editorContainerRef.el.scrollTop = 0;
                }
            }, 500);
        }
    }

    async acknowledgeReading() {
        if (!this.state.pendingReadingId) return;
        try {
            await this.orm.call("info.hub.article.reading", "action_acknowledge", [[this.state.pendingReadingId]]);
            this.state.pendingReadingId = null;
        } catch (e) {
            this.notification.add("Failed to record acknowledgement.", { type: "danger" });
        }
    }

    _checkScrollToTop() {
        if (this.state.activeArticleId) {
            if (this.state.activeArticleId !== this.lastScrolledArticleId) {
                if (this.editorContainerRef.el) {
                    this.editorContainerRef.el.scrollTop = 0;
                    this.lastScrolledArticleId = this.state.activeArticleId;
                }
            }
        } else {
            this.lastScrolledArticleId = null;
        }
    }

    get breadcrumbs() {
        if (!this.state.activeArticle || !this.state.articles.length) {
            return [];
        }
        const crumbs = [];
        let current = this.state.activeArticle;

        while (current && current.parent_id) {
            const parentId = Array.isArray(current.parent_id) ? current.parent_id[0] : current.parent_id;
            const parentName = Array.isArray(current.parent_id) ? current.parent_id[1] : '';

            const parentArticle = this.state.articles.find(a => a.id === parentId);
            if (parentArticle) {
                crumbs.unshift({
                    id: parentArticle.id,
                    name: parentArticle.name || 'Untitled',
                });
                current = parentArticle;
            } else {
                crumbs.unshift({
                    id: parentId,
                    name: parentName || 'Untitled',
                });
                break;
            }
        }
        return crumbs;
    }

    async joinArticle() {
        if (!this.state.activeArticleId) return;
        try {
            await this.orm.call("info.hub.article", "action_join_article", [[this.state.activeArticleId]]);
            await this._loadData();
            await this.selectArticle(this.state.activeArticleId, false);
        } catch {
            this.notification.add("Failed to join article.", { type: "danger" });
        }
    }

    async onCloseTemplateEdit() {
        if (this.state.articles && this.state.articles.length > 0) {
            await this.selectArticle(this.state.articles[0].id);
        } else {
            this.state.activeArticleId = null;
            this.state.activeArticle = null;
            router.pushState({ article_id: null });
        }
    }

    // -------------------------------------------------------------------------
    // Hidden Articles (eye icon)
    // -------------------------------------------------------------------------

    /**
     * Opens the Hidden Articles picker dialog.
     * Called when the user clicks the eye (👁) icon in the Workspace section title.
     */
    searchHiddenArticles() {
        this.state.showHiddenArticlesDialog = true;
    }

    async onHiddenArticleJoined(articleId) {
        this.state.showHiddenArticlesDialog = false;
        await this._loadData();
        await this.selectArticle(articleId);
    }

    goBack() {
        if (this.state.historyIndex > 0) {
            this.state.historyIndex--;
            const articleId = this.state.history[this.state.historyIndex];
            this.selectArticle(articleId, false);
        }
    }

    goForward() {
        if (this.state.historyIndex < this.state.history.length - 1) {
            this.state.historyIndex++;
            const articleId = this.state.history[this.state.historyIndex];
            this.selectArticle(articleId, false);
        }
    }

    _closeEditorPowerbox() {
        this.state.showSlashMenu = false;
        if (this.editor) {
            try {
                this.editor.shared.powerbox?.closePowerbox();
            } catch (e) {
            }
        }
    }

    onAddProperty() {
        this._closeEditorPowerbox();
        this.state.editingPropertyIndex = null;
        this.state.newPropertyLabel = `Property ${this.state.customProperties.length + 1}`;
        this.state.newPropertyType = "Text";
        this.state.showFieldTypeDropdown = false;
        this.state.newPropertySelectionValues = [];
        this.state.newPropertyTags = [];
        this.state.newPropertyModel = "";
        this.state.newPropertySuffix = "";
        this.state.newPropertyDisplayInCards = false;
        this.state.newPropertyDefaultValue = "";
        this.state.newPropertyDefaultValueId = null;
        this.state.newPropertyDefaultValueM2mRecords = [];
        this.state.showPopupDefaultValueDropdown = false;
        this.state.popupDefaultValueRecords = [];
        this.state.tagCreationQuery = "";
        this._htmlPopupEditor = null;
        this.state.htmlPopupEditorKey++;
        this.state.showAddPropertyPopup = !this.state.showAddPropertyPopup;
    }

    onMenuAddProperty() {
        if (!this.state.activeArticleId || !this.state.activeArticle.parent_id) return;
        this._closeEditorPowerbox();
        this.state.showPropertiesPanel = true;
        this.state.editingPropertyIndex = null;
        this.state.newPropertyLabel = `Property ${this.state.customProperties.length + 1}`;
        this.state.newPropertyType = "Text";
        this.state.showFieldTypeDropdown = false;
        this.state.newPropertySelectionValues = [];
        this.state.newPropertyTags = [];
        this.state.newPropertyModel = "";
        this.state.newPropertySuffix = "";
        this.state.newPropertyDisplayInCards = false;
        this.state.newPropertyDefaultValue = "";
        this.state.newPropertyDefaultValueId = null;
        this.state.newPropertyDefaultValueM2mRecords = [];
        this.state.showPopupDefaultValueDropdown = false;
        this.state.popupDefaultValueRecords = [];
        this.state.tagCreationQuery = "";
        this.state.showAddPropertyPopup = true;
    }

    onEditProperty(index) {
        if (this.state.isLocked) return;
        this._closeEditorPowerbox();
        const prop = this.state.customProperties[index];
        this.state.editingPropertyIndex = index;
        this.state.newPropertyLabel = prop.label;
        this.state.newPropertyType = prop.type;
        this.state.showFieldTypeDropdown = false;
        this.state.newPropertySelectionValues = prop.selectionValues ? JSON.parse(JSON.stringify(prop.selectionValues)) : [];
        this.state.newPropertyTags = prop.tags ? JSON.parse(JSON.stringify(prop.tags)) : [];
        this.state.newPropertyModel = prop.model || "";
        this.state.domainRules = prop.domainRules ? JSON.parse(JSON.stringify(prop.domainRules)) : [];
        this.state.domainMatchType = prop.domainMatchType || "all";
        this.state.domainIncludeArchived = !!prop.domainIncludeArchived;
        this.state.newSeparatorState = prop.separatorState || "open";
        this.state.newPropertySuffix = prop.suffix || "";
        this.state.newPropertyDisplayInCards = !!prop.displayInCards;
        this.state.newPropertyDefaultValue = prop.defaultValue || "";
        this.state.newPropertyDefaultValueId = prop.defaultValueId || null;
        this.state.newPropertyDefaultValueM2mRecords = prop.defaultValueM2mRecords ? JSON.parse(JSON.stringify(prop.defaultValueM2mRecords)) : [];
        this.state.showPopupDefaultValueDropdown = false;
        this.state.popupDefaultValueRecords = [];
        this.state.tagCreationQuery = "";
        this.state.domainRecordCount = null;
        this._htmlPopupEditor = null;
        this.state.htmlPopupEditorKey++;
        this.state.showAddPropertyPopup = true;
        this._fetchDomainRecordCount();
    }

    onPropertyLabelChange(ev) {
        this.state.newPropertyLabel = ev.target.value;
    }

    saveAndClosePopup(shouldClose = true) {
        if (this.state.newPropertyType === 'HTML' && this._htmlPopupEditor) {
            const el = this._htmlPopupEditor.editable || this._htmlPopupEditor.getElContent?.();
            if (el) {
                this.state.newPropertyDefaultValue = el.innerHTML || "";
            }
        }
        if (this.state.newPropertyLabel.trim()) {
            if (this.state.newPropertyType === 'Selection') {
                const defVal = this.state.newPropertySelectionValues.find(v => v.isDefault);
                this.state.newPropertyDefaultValue = defVal ? defVal.name : "";
            }
            if (this.state.editingPropertyIndex !== null) {
                const prop = this.state.customProperties[this.state.editingPropertyIndex];
                prop.label = this.state.newPropertyLabel.trim();
                const typeChanged = prop.type !== this.state.newPropertyType;
                prop.type = this.state.newPropertyType;
                const oldDefaultVal = prop.defaultValue;
                prop.defaultValue = this.state.newPropertyDefaultValue;
                prop.defaultValueId = this.state.newPropertyDefaultValueId || null;
                prop.defaultValueM2mRecords = this.state.newPropertyDefaultValueM2mRecords ? JSON.parse(JSON.stringify(this.state.newPropertyDefaultValueM2mRecords)) : [];
                if (typeChanged || prop.value === undefined || prop.value === null || prop.value === "" || prop.value === oldDefaultVal) {
                    prop.value = this.state.newPropertyDefaultValue || "";
                    prop.recordId = this.state.newPropertyDefaultValueId || null;
                }
                if (!prop.m2mRecords || prop.m2mRecords.length === 0) {
                    prop.m2mRecords = this.state.newPropertyDefaultValueM2mRecords ? JSON.parse(JSON.stringify(this.state.newPropertyDefaultValueM2mRecords)) : [];
                }
                prop.selectionValues = JSON.parse(JSON.stringify(this.state.newPropertySelectionValues));
                prop.tags = JSON.parse(JSON.stringify(this.state.newPropertyTags));
                prop.model = this.state.newPropertyModel;
                prop.domainRules = JSON.parse(JSON.stringify(this.state.domainRules));
                prop.domainMatchType = this.state.domainMatchType;
                prop.domainIncludeArchived = this.state.domainIncludeArchived;
                prop.separatorState = this.state.newSeparatorState;
                prop.suffix = this.state.newPropertySuffix;
                prop.displayInCards = this.state.newPropertyDisplayInCards;
            } else {
                this.state.customProperties.push({
                    label: this.state.newPropertyLabel.trim(),
                    type: this.state.newPropertyType,
                    defaultValue: this.state.newPropertyDefaultValue,
                    defaultValueId: this.state.newPropertyDefaultValueId || null,
                    defaultValueM2mRecords: this.state.newPropertyDefaultValueM2mRecords ? JSON.parse(JSON.stringify(this.state.newPropertyDefaultValueM2mRecords)) : [],
                    value: this.state.newPropertyDefaultValue || "",
                    recordId: this.state.newPropertyDefaultValueId || null,
                    m2mRecords: this.state.newPropertyDefaultValueM2mRecords ? JSON.parse(JSON.stringify(this.state.newPropertyDefaultValueM2mRecords)) : [],
                    separatorState: this.state.newSeparatorState,
                    suffix: this.state.newPropertySuffix,
                    displayInCards: this.state.newPropertyDisplayInCards,
                    selectionValues: JSON.parse(JSON.stringify(this.state.newPropertySelectionValues)),
                    tags: JSON.parse(JSON.stringify(this.state.newPropertyTags)),
                    model: this.state.newPropertyModel,
                    domainRules: JSON.parse(JSON.stringify(this.state.domainRules)),
                    domainMatchType: this.state.domainMatchType,
                    domainIncludeArchived: this.state.domainIncludeArchived
                });
            }
            this._syncParentPropertyMap();
            this.state.editorDirty = true;
        }
        if (shouldClose) {
            this.state.showAddPropertyPopup = false;
            this.state.showFieldTypeDropdown = false;
            this.state.editingPropertyIndex = null;
        }
    }

    updateCustomPropertyValue(prop, value) {
        prop.value = value;
        this.state.editorDirty = true;
        this._persistCurrentArticlePropertyValues();
    }

    getHtmlPropEditorConfig(context, propIndex) {
        const initialContent = context === 'popup'
            ? (this.state.newPropertyDefaultValue || "")
            : (propIndex !== undefined && this.state.customProperties[propIndex]
                ? (this.state.customProperties[propIndex].value || "")
                : "");

        return {
            content: markup(initialContent),
            Plugins: [
                ...MAIN_PLUGINS,
            ],
            onChange: () => {
                if (context === 'popup') {
                    const editor = this._htmlPopupEditor;
                    if (editor) {
                        const el = editor.editable || editor.getElContent?.();
                        if (el) {
                            this.state.newPropertyDefaultValue = el.innerHTML || "";
                        }
                    }
                } else if (context === 'value' && propIndex !== undefined) {
                    const editor = this._htmlValueEditors[propIndex];
                    if (editor) {
                        const el = editor.editable || editor.getElContent?.();
                        if (el) {
                            const prop = this.state.customProperties[propIndex];
                            if (prop) {
                                prop.value = el.innerHTML || "";
                                this.state.editorDirty = true;
                                this._persistCurrentArticlePropertyValues();
                            }
                        }
                    }
                }
            },
        };
    }

    onHtmlPopupEditorLoad(editor) {
        this._htmlPopupEditor = editor;
        if (editor && editor.editable) {
            editor.editable.addEventListener("keydown", (ev) => {
                ev.stopPropagation();
            }, { capture: true });
            editor.editable.addEventListener("keyup", (ev) => {
                ev.stopPropagation();
            }, { capture: true });
        }
    }

    onHtmlValueEditorLoad(editor, propIndex) {
        this._htmlValueEditors[propIndex] = editor;
    }

    toggleSeparator(index) {
        const prop = this.state.customProperties[index];
        if (prop) {
            prop.separatorState = prop.separatorState === 'fold' ? 'open' : 'fold';
            this._syncParentPropertyMap();
        }
    }

    isPropertyVisible(index) {
        const properties = this.state.customProperties;
        const prop = properties[index];
        if (!prop) return false;
        if (prop.type === 'Separator') return true;
        // Traverse backwards to find the nearest preceding Separator
        for (let i = index - 1; i >= 0; i--) {
            if (properties[i].type === 'Separator') {
                return properties[i].separatorState !== 'fold';
            }
        }
        return true;
    }

    openSignaturePopup(index) {
        if (this.state.isLocked) return;
        this.state.activeSignaturePropIndex = index;
        this.state.sigTab = "draw";
        this.state.sigLoadedImage = null;
        this.state.showSignaturePopup = true;
        setTimeout(() => this._initSigCanvas(), 50);
    }

    closeSignaturePopup() {
        this.state.showSignaturePopup = false;
        this.state.activeSignaturePropIndex = null;
        this._sigDrawing = false;
    }

    switchSigTab(tab) {
        this.state.sigTab = tab;
        if (tab === "draw") {
            setTimeout(() => this._initSigCanvas(), 50);
        }
    }

    _initSigCanvas() {
        const canvas = document.getElementById("o_info_hub_sig_canvas");
        if (!canvas) return;
        const rect = canvas.getBoundingClientRect();
        canvas.width = rect.width * window.devicePixelRatio;
        canvas.height = rect.height * window.devicePixelRatio;
        const ctx = canvas.getContext("2d");
        ctx.scale(window.devicePixelRatio, window.devicePixelRatio);
        ctx.fillStyle = "#111827";
        ctx.fillRect(0, 0, rect.width, rect.height);
        this._sigCtx = ctx;
        this._sigCanvas = canvas;
        this._sigDrawing = false;
    }

    sigStartDraw(ev) {
        if (!this._sigCtx) return;
        this._sigDrawing = true;
        const pos = this._getSigPos(ev);
        this._sigCtx.beginPath();
        this._sigCtx.moveTo(pos.x, pos.y);
        ev.currentTarget.setPointerCapture(ev.pointerId);
    }

    sigDraw(ev) {
        if (!this._sigDrawing || !this._sigCtx) return;
        const pos = this._getSigPos(ev);
        this._sigCtx.lineWidth = 2.5;
        this._sigCtx.lineCap = "round";
        this._sigCtx.strokeStyle = "#1e3a8a";
        this._sigCtx.lineTo(pos.x, pos.y);
        this._sigCtx.stroke();
    }

    sigStopDraw() {
        this._sigDrawing = false;
    }

    _getSigPos(ev) {
        const canvas = this._sigCanvas;
        const rect = canvas.getBoundingClientRect();
        return { x: ev.clientX - rect.left, y: ev.clientY - rect.top };
    }

    clearSignature() {
        if (this.state.sigTab === "draw" && this._sigCtx && this._sigCanvas) {
            const rect = this._sigCanvas.getBoundingClientRect();
            this._sigCtx.fillStyle = "#111827";
            this._sigCtx.fillRect(0, 0, rect.width, rect.height);
        } else {
            this.state.sigLoadedImage = null;
        }
    }

    onSigFileLoad(ev) {
        const file = ev.target.files[0];
        if (!file) return;
        const reader = new FileReader();
        reader.onload = (e) => { this.state.sigLoadedImage = e.target.result; };
        reader.readAsDataURL(file);
    }

    adoptSignature() {
        const index = this.state.activeSignaturePropIndex;
        const prop = this.state.customProperties[index];
        if (!prop) { this.closeSignaturePopup(); return; }

        if (this.state.sigTab === "draw" && this._sigCanvas) {
            prop.signatureData = this._sigCanvas.toDataURL("image/png");
        } else if (this.state.sigTab === "load" && this.state.sigLoadedImage) {
            prop.signatureData = this.state.sigLoadedImage;
        }
        this.state.editorDirty = true;
        this._persistCurrentArticlePropertyValues();
        this.closeSignaturePopup();
    }

    async onM2oFocus(index) {
        const prop = this.state.customProperties[index];
        if (!prop) return;
        if (prop.type !== 'Tags' && !prop.model) return;
        this.state.activeM2oPropIndex = index;
        this.state.m2oSearchQuery = prop.type === 'Tags' ? "" : (prop.value || "");
        if (prop.type !== 'Tags') {
            await this._fetchM2oRecords(index);
        }
    }

    onM2oBlur(index) {
        setTimeout(() => {
            if (this.state.activeM2oPropIndex === index) {
                this.state.activeM2oPropIndex = null;
            }
        }, 200);
    }

    async onM2oInput(index, ev) {
        const prop = this.state.customProperties[index];
        if (!prop) return;
        const val = ev.target.value;
        this.state.m2oSearchQuery = val;
        if (prop.type !== 'Tags') {
            prop.value = val;
            await this._fetchM2oRecords(index);
        }
    }

    onTagsInputKeydown(index, ev) {
        const prop = this.state.customProperties[index];
        if (!prop || prop.type !== 'Tags') return;
        if (ev.key === "Enter") {
            ev.preventDefault();
            const query = String(this.state.m2oSearchQuery || "").trim();
            if (!query) return;
            const existing = (prop.tags || []).find(
                (t) => t.name.toLowerCase() === query.toLowerCase()
            );
            if (existing) {
                this.selectTag(index, existing);
            } else {
                this.createAndSelectTag(index, query);
            }
        } else if (ev.key === "Backspace" && !ev.target.value) {
            if (Array.isArray(prop.value) && prop.value.length > 0) {
                this.removeTagValue(index, prop.value[prop.value.length - 1]);
            }
        } else if (ev.key === "Escape") {
            this.state.activeM2oPropIndex = null;
            ev.target.blur();
        }
    }

    tagExists(prop, name) {
        const lower = String(name || "").trim().toLowerCase();
        if (!lower) return true;
        return (prop.tags || []).some((t) => t.name.toLowerCase() === lower);
    }

    createAndSelectTag(index, name) {
        const prop = this.state.customProperties[index];
        if (!prop) return;
        const trimmed = String(name || "").trim();
        if (!trimmed) return;
        if (!Array.isArray(prop.tags)) prop.tags = [];
        if (!Array.isArray(prop.value)) prop.value = [];

        let tag = prop.tags.find((t) => t.name.toLowerCase() === trimmed.toLowerCase());
        if (!tag) {
            tag = { id: `tag_${Date.now()}_${Math.floor(Math.random() * 10000)}`, name: trimmed };
            prop.tags.push(tag);
        }
        if (!prop.value.includes(tag.name)) {
            prop.value.push(tag.name);
        }
        this.state.m2oSearchQuery = "";
        this.state.editorDirty = true;
        this._syncParentPropertyMap();
    }

    async _fetchM2oRecords(index) {
        const prop = this.state.customProperties[index];
        if (!prop || !prop.model) return;
        const technicalModel = this.state.availableModelDetails
            ? this.state.availableModelDetails[prop.model]
            : null;
        if (!technicalModel) return;

        try {
            const domain = [];
            if (prop.domainRules && prop.domainRules.length > 0) {
                const rules = prop.domainRules
                    .filter(r => r.field && r.operator && r.value !== "")
                    .map(r => [r.field, r.operator, r.value]);
                if (prop.domainMatchType === "any" && rules.length > 1) {
                    for (let i = 0; i < rules.length - 1; i++) {
                        domain.push("|");
                    }
                    domain.push(...rules);
                } else {
                    domain.push(...rules);
                }
            }

            const searchDomain = [...domain];
            if (this.state.m2oSearchQuery) {
                searchDomain.push(["display_name", "ilike", this.state.m2oSearchQuery]);
            }

            const kwargs = { limit: 8 };
            if (prop.domainIncludeArchived) {
                kwargs.context = { active_test: false };
            }

            const records = await this.orm.searchRead(
                technicalModel,
                searchDomain,
                ["id", "display_name"],
                kwargs
            );
            this.state.m2oRecords = records;
        } catch {
            this.state.m2oRecords = [];
        }
    }

    selectM2oRecord(index, record) {
        const prop = this.state.customProperties[index];
        if (prop) {
            prop.value = record.display_name;
            prop.recordId = record.id;
            this.state.editorDirty = true;
            this._persistCurrentArticlePropertyValues();
        }
        this.state.activeM2oPropIndex = null;
    }

    async onPopupDefaultValueFocus() {
        if (!this.state.newPropertyModel) return;
        this.state.showPopupDefaultValueDropdown = true;
        await this._fetchPopupDefaultValueRecords();
    }

    onPopupDefaultValueBlur() {
        setTimeout(() => {
            this.state.showPopupDefaultValueDropdown = false;
        }, 200);
    }

    async onPopupDefaultValueInput(ev) {
        this.state.newPropertyDefaultValue = ev.target.value;
        await this._fetchPopupDefaultValueRecords();
    }

    async _fetchPopupDefaultValueRecords() {
        if (!this.state.newPropertyModel) {
            this.state.popupDefaultValueRecords = [];
            return;
        }
        const technicalModel = this.state.availableModelDetails
            ? this.state.availableModelDetails[this.state.newPropertyModel]
            : null;
        if (!technicalModel) {
            this.state.popupDefaultValueRecords = [];
            return;
        }

        try {
            const domain = [];
            if (this.state.domainRules && this.state.domainRules.length > 0) {
                const rules = this.state.domainRules
                    .filter(r => r.field && r.operator && r.value !== "")
                    .map(r => [r.field, r.operator, r.value]);
                if (this.state.domainMatchType === "any" && rules.length > 1) {
                    for (let i = 0; i < rules.length - 1; i++) {
                        domain.push("|");
                    }
                    domain.push(...rules);
                } else {
                    domain.push(...rules);
                }
            }

            const searchDomain = [...domain];
            if (this.state.newPropertyDefaultValue) {
                searchDomain.push(["display_name", "ilike", this.state.newPropertyDefaultValue]);
            }

            const kwargs = { limit: 8 };
            if (this.state.domainIncludeArchived) {
                kwargs.context = { active_test: false };
            }

            const records = await this.orm.searchRead(
                technicalModel,
                searchDomain,
                ["id", "display_name"],
                kwargs
            );
            this.state.popupDefaultValueRecords = records;
        } catch {
            this.state.popupDefaultValueRecords = [];
        }
    }

    selectPopupDefaultValueRecord(record) {
        this.state.newPropertyDefaultValue = record.display_name;
        this.state.newPropertyDefaultValueId = record.id;
        this.state.showPopupDefaultValueDropdown = false;
    }

    selectPopupDefaultValueM2mRecord(record) {
        if (!this.state.newPropertyDefaultValueM2mRecords) {
            this.state.newPropertyDefaultValueM2mRecords = [];
        }
        if (!this.state.newPropertyDefaultValueM2mRecords.some(r => r.id === record.id)) {
            this.state.newPropertyDefaultValueM2mRecords.push(record);
        }
        this.state.newPropertyDefaultValue = "";
        this.state.showPopupDefaultValueDropdown = false;
    }

    removePopupDefaultValueM2mRecord(recordId) {
        if (this.state.newPropertyDefaultValueM2mRecords) {
            this.state.newPropertyDefaultValueM2mRecords = this.state.newPropertyDefaultValueM2mRecords.filter(r => r.id !== recordId);
        }
    }

    onSelectPopupDefaultValueRecord(record) {
        if (this.state.newPropertyType === 'Many2many') {
            const already = (this.state.newPropertyDefaultValueM2mRecords || []).some(r => r.id === record.id);
            if (!already) {
                this.selectPopupDefaultValueM2mRecord(record);
            } else {
                this.state.showPopupDefaultValueDropdown = false;
            }
        } else {
            this.selectPopupDefaultValueRecord(record);
        }
    }

    selectM2mRecord(index, record) {
        const prop = this.state.customProperties[index];
        if (prop) {
            if (!prop.m2mRecords) prop.m2mRecords = [];
            if (!prop.m2mRecords.some(r => r.id === record.id)) {
                prop.m2mRecords.push(record);
                this.state.editorDirty = true;
                this._persistCurrentArticlePropertyValues();
            }
            this.state.m2oSearchQuery = "";
        }
    }

    removeM2mRecord(index, recordId) {
        const prop = this.state.customProperties[index];
        if (prop && prop.m2mRecords) {
            prop.m2mRecords = prop.m2mRecords.filter(r => r.id !== recordId);
            this.state.editorDirty = true;
            this._persistCurrentArticlePropertyValues();
        }
    }

    selectTag(index, tag) {
        const prop = this.state.customProperties[index];
        if (prop) {
            if (!Array.isArray(prop.value)) prop.value = [];
            if (!prop.value.includes(tag.name)) {
                prop.value.push(tag.name);
                this.state.editorDirty = true;
                this._persistCurrentArticlePropertyValues();
            }
            this.state.m2oSearchQuery = "";
        }
    }

    removeTagValue(index, tagName) {
        const prop = this.state.customProperties[index];
        if (prop && Array.isArray(prop.value)) {
            prop.value = prop.value.filter(val => val !== tagName);
            this.state.editorDirty = true;
            this._persistCurrentArticlePropertyValues();
        }
    }

    getFilteredTags(prop) {
        const selected = Array.isArray(prop.value) ? prop.value : [];
        const query = String(this.state.m2oSearchQuery || "").toLowerCase().trim();
        const tags = prop.tags || [];
        return tags.filter(tag => {
            const isNotSelected = !selected.includes(tag.name);
            const matchesQuery = !query || tag.name.toLowerCase().includes(query);
            return isNotSelected && matchesQuery;
        });
    }

    openM2oSearchMore(index) {
        const prop = this.state.customProperties[index];
        if (!prop || !prop.model) return;
        const technicalModel = this.state.availableModelDetails
            ? this.state.availableModelDetails[prop.model]
            : null;
        if (!technicalModel) return;

        const domain = [];
        if (prop.domainRules && prop.domainRules.length > 0) {
            const rules = prop.domainRules
                .filter(r => r.field && r.operator && r.value !== "")
                .map(r => [r.field, r.operator, r.value]);
            if (prop.domainMatchType === "any" && rules.length > 1) {
                for (let i = 0; i < rules.length - 1; i++) {
                    domain.push("|");
                }
                domain.push(...rules);
            } else {
                domain.push(...rules);
            }
        }
        if (this.state.m2oSearchQuery) {
            domain.push(["display_name", "ilike", this.state.m2oSearchQuery]);
        }

        const context = {};
        if (prop.domainIncludeArchived) {
            context.active_test = false;
        }

        this.action.doAction({
            type: "ir.actions.act_window",
            name: `Search: ${prop.model}`,
            res_model: technicalModel,
            domain: domain,
            context: context,
            views: [[false, "list"], [false, "form"]],
            target: "new",
        });
        this.state.activeM2oPropIndex = null;
    }

    cancelProperty() {
        if (this.state.editingPropertyIndex !== null) {
            this.state.customProperties.splice(this.state.editingPropertyIndex, 1);
            this._syncParentPropertyMap();
        }
        this.state.showAddPropertyPopup = false;
        this.state.showFieldTypeDropdown = false;
        this.state.editingPropertyIndex = null;
    }

    discardProperty(ev) {
        if (ev) {
            ev.stopPropagation();
            ev.preventDefault();
        }
        this.state.showAddPropertyPopup = false;
        this.state.showFieldTypeDropdown = false;
        this.state.editingPropertyIndex = null;
    }

    toggleFieldTypeDropdown() {
        this.state.showFieldTypeDropdown = !this.state.showFieldTypeDropdown;
    }

    selectFieldType(typeName) {
        const type = this.getFieldTypes().find(t => t.name === typeName);
        if (type && type.disabled) return;
        const prevType = this.state.newPropertyType;
        this.state.newPropertyType = typeName;
        this.state.showFieldTypeDropdown = false;
        if (typeName === 'HTML' || prevType === 'HTML') {
            this.state.newPropertyDefaultValue = "";
            this._htmlPopupEditor = null;
            this.state.htmlPopupEditorKey++;
        }
    }

    onAddSelectionValue() {
        this.state.newPropertySelectionValues.push({ id: Date.now(), name: "", isDefault: false });
    }

    onSelectionValueChange(id, value) {
        const val = this.state.newPropertySelectionValues.find(v => v.id === id);
        if (val) val.name = value;
    }

    onRemoveSelectionValue(id) {
        this.state.newPropertySelectionValues = this.state.newPropertySelectionValues.filter(v => v.id !== id);
    }

    onToggleSelectionDefault(id) {
        this.state.newPropertySelectionValues.forEach(v => {
            v.isDefault = (v.id === id) ? !v.isDefault : false;
        });
    }

    onTagKeydown(ev) {
        if (ev.key === "Enter" && ev.target.value.trim()) {
            ev.preventDefault();
            const tagName = ev.target.value.trim();
            if (!this.state.newPropertyTags.some(t => t.name.toLowerCase() === tagName.toLowerCase())) {
                this.state.newPropertyTags.push({ id: Date.now(), name: tagName });
            }
            ev.target.value = "";
            this.state.tagCreationQuery = "";
        } else if (ev.key === "Backspace" && !ev.target.value && this.state.newPropertyTags.length > 0) {
            this.state.newPropertyTags.pop();
        }
    }

    onCreateTagDropdown(tagName) {
        if (!tagName.trim()) return;
        const name = tagName.trim();
        if (!this.state.newPropertyTags.some(t => t.name.toLowerCase() === name.toLowerCase())) {
            this.state.newPropertyTags.push({ id: Date.now(), name: name });
        }
        this.state.tagCreationQuery = "";
        this.state.tagsFocused = false;
    }

    onTagCreationBlur() {
        setTimeout(() => {
            this.state.tagsFocused = false;
        }, 200);
    }

    onRemoveTag(id) {
        this.state.newPropertyTags = this.state.newPropertyTags.filter(t => t.id !== id);
    }

    selectModel(modelName) {
        this.state.newPropertyModel = modelName;
        this.state.showModelDropdown = false;
        this.state.domainRules = [];
        this.state.domainMatchType = "all";
        this.state.domainIncludeArchived = false;
        this.state.domainRecordCount = null;
        this.state.newPropertyDefaultValue = "";
        this.state.newPropertyDefaultValueId = null;
        this.state.newPropertyDefaultValueM2mRecords = [];
        this._fetchDomainRecordCount();
    }

    onModelBlur() {
        setTimeout(() => {
            this.state.showModelDropdown = false;
        }, 200);
    }

    async _fetchDomainRecordCount() {
        if (!this.state.newPropertyModel) return;
        const technicalModel = this.state.availableModelDetails
            ? this.state.availableModelDetails[this.state.newPropertyModel]
            : null;
        if (!technicalModel) {
            this.state.domainRecordCount = null;
            return;
        }
        try {
            const domain = this._buildDomain();
            const kwargs = {};
            if (this.state.domainIncludeArchived) {
                kwargs.context = { active_test: false };
            }
            const count = await this.orm.call(technicalModel, "search_count", [domain], kwargs);
            this.state.domainRecordCount = count;
        } catch {
            this.state.domainRecordCount = null;
        }
    }

    _buildDomain() {
        const rules = this.state.domainRules
            .filter(r => r.field && r.operator && r.value !== "")
            .map(r => [r.field, r.operator, r.value]);
        if (this.state.domainMatchType === "any" && rules.length > 1) {
            const domain = [];
            for (let i = 0; i < rules.length - 1; i++) {
                domain.push("|");
            }
            return domain.concat(rules);
        }
        return rules;
    }

    _saveCurrentArticlePropertyValues() {
        const articleId = this.state.activeArticleId;
        if (!articleId || !this.state.customProperties.length) return;
        const values = {};
        for (const prop of this.state.customProperties) {
            values[prop.label] = {
                value: prop.value ?? "",
                m2mRecords: prop.m2mRecords ? [...prop.m2mRecords] : [],
                signatureData: prop.signatureData || null,
                recordId: prop.recordId || null,
            };
        }
        this.state.articlePropertyValues[articleId] = values;
        this._persistCurrentArticlePropertyValues();
    }

    _persistCurrentArticlePropertyValues() {
        const articleId = this.state.activeArticleId;
        const activeArticle = this.state.activeArticle;
        if (!articleId || !activeArticle || !activeArticle.parent_id) return;
        const parentId = Array.isArray(activeArticle.parent_id)
            ? activeArticle.parent_id[0]
            : activeArticle.parent_id;
        const values = {};
        for (const prop of this.state.customProperties) {
            values[prop.label] = {
                value: prop.value ?? "",
                m2mRecords: prop.m2mRecords ? [...prop.m2mRecords] : [],
                signatureData: prop.signatureData || null,
                recordId: prop.recordId || null,
            };
        }
        this.state.articlePropertyValues[articleId] = values;
        const defs = this.state.parentPropertyMap[parentId] || [];
        this.orm.call(
            'info.hub.article',
            'save_article_properties',
            [articleId, parentId, defs, values]
        ).then(() => {
            this._updateLastEditedMeta();
        }).catch(() => {});
    }

    async _updateLastEditedMeta() {
        if (!this.state.activeArticleId) return;
        try {
            const [extra] = await this.orm.read(
                "info.hub.article",
                [this.state.activeArticleId],
                ["last_edition_uid", "last_edition_date"]
            );
            if (this.state.activeArticle) {
                this.state.activeArticle.last_edition_uid = extra.last_edition_uid;
                this.state.activeArticle.last_edition_date = extra.last_edition_date;
            }
        } catch (e) {
            console.warn("Failed to update last edited metadata:", e);
        }
    }

    async _loadPropertiesForArticle(articleId, parentId) {
        if (!parentId) {
            this.state.customProperties = [];
            return;
        }
        if (!this.state.parentPropertyMap[parentId]) {
            try {
                const result = await this.orm.call(
                    'info.hub.article',
                    'load_article_properties',
                    [articleId, parentId]
                );
                this.state.parentPropertyMap[parentId] = result.property_defs || [];
                this.state.articlePropertyValues[articleId] = result.property_values || {};
            } catch {
                this.state.parentPropertyMap[parentId] = [];
            }
        } else if (!this.state.articlePropertyValues[articleId]) {
            try {
                const result = await this.orm.call(
                    'info.hub.article',
                    'load_article_properties',
                    [articleId, parentId]
                );
                this.state.articlePropertyValues[articleId] = result.property_values || {};
            } catch {
                this.state.articlePropertyValues[articleId] = {};
            }
        }
        const defs = this.state.parentPropertyMap[parentId] || [];
        const savedValues = this.state.articlePropertyValues[articleId] || {};
        this.state.customProperties = defs.map(def => {
            let val = (def.label in savedValues && savedValues[def.label].value !== undefined && savedValues[def.label].value !== null && savedValues[def.label].value !== "")
                ? savedValues[def.label].value
                : (def.defaultValue ?? "");
            if (def.type === 'Tags') {
                if (typeof val === 'string') {
                    val = val ? val.split(',').map(s => s.trim()) : [];
                } else if (!Array.isArray(val)) {
                    val = [];
                }
            }
            return {
                ...def,
                value: val,
                m2mRecords: savedValues[def.label]?.m2mRecords
                    ? [...savedValues[def.label].m2mRecords]
                    : (def.defaultValueM2mRecords ? [...def.defaultValueM2mRecords] : []),
                signatureData: savedValues[def.label]?.signatureData || null,
                recordId: (def.label in savedValues && savedValues[def.label].recordId !== undefined && savedValues[def.label].recordId !== null)
                    ? savedValues[def.label].recordId
                    : (def.defaultValueId ?? null),
            };
        });
    }

    _syncParentPropertyMap() {
        const activeArticle = this.state.activeArticle;
        if (!activeArticle || !activeArticle.parent_id) return;
        const articleId = this.state.activeArticleId;
        const parentId = Array.isArray(activeArticle.parent_id)
            ? activeArticle.parent_id[0]
            : activeArticle.parent_id;
        const defs = this.state.customProperties.map(p => ({
            label: p.label,
            type: p.type,
            defaultValue: p.defaultValue || "",
            defaultValueId: p.defaultValueId || null,
            defaultValueM2mRecords: p.defaultValueM2mRecords ? JSON.parse(JSON.stringify(p.defaultValueM2mRecords)) : [],
            selectionValues: p.selectionValues ? JSON.parse(JSON.stringify(p.selectionValues)) : [],
            tags: p.tags ? JSON.parse(JSON.stringify(p.tags)) : [],
            model: p.model || "",
            domainRules: p.domainRules ? JSON.parse(JSON.stringify(p.domainRules)) : [],
            domainMatchType: p.domainMatchType || "all",
            domainIncludeArchived: !!p.domainIncludeArchived,
            separatorState: p.separatorState || "open",
            suffix: p.suffix || "",
            displayInCards: !!p.displayInCards,
        }));
        this.state.parentPropertyMap[parentId] = defs;
        const values = {};
        for (const prop of this.state.customProperties) {
            values[prop.label] = {
                value: prop.value ?? "",
                m2mRecords: prop.m2mRecords ? [...prop.m2mRecords] : [],
                signatureData: prop.signatureData || null,
                recordId: prop.recordId || null,
            };
        }
        this.state.articlePropertyValues[articleId] = values;
        this.orm.call(
            'info.hub.article',
            'save_article_properties',
            [articleId, parentId, defs, values]
        ).catch(() => {});
    }

    onAddDomainRule() {
        this.state.domainRules.push({ id: Date.now(), field: "id", operator: "=", value: "1" });
        this._fetchDomainRecordCount();
    }

    onRemoveDomainRule(id) {
        this.state.domainRules = this.state.domainRules.filter(r => r.id !== id);
        this._fetchDomainRecordCount();
    }

    onDomainRuleFieldChange(id, value) {
        const rule = this.state.domainRules.find(r => r.id === id);
        if (rule) { rule.field = value; this._fetchDomainRecordCount(); }
    }

    onDomainRuleOperatorChange(id, value) {
        const rule = this.state.domainRules.find(r => r.id === id);
        if (rule) { rule.operator = value; this._fetchDomainRecordCount(); }
    }

    onDomainRuleValueChange(id, value) {
        const rule = this.state.domainRules.find(r => r.id === id);
        if (rule) { rule.value = value; this._fetchDomainRecordCount(); }
    }

    openDomainRecords() {
        if (!this.state.newPropertyModel || this.state.domainRecordCount === null || this.state.domainRecordCount === 0) return;
        const technicalModel = this.state.availableModelDetails
            ? this.state.availableModelDetails[this.state.newPropertyModel]
            : null;
        if (!technicalModel) return;

        const domain = this._buildDomain();
        const context = {};
        if (this.state.domainIncludeArchived) {
            context.active_test = false;
        }

        this.action.doAction({
            type: "ir.actions.act_window",
            name: `${this.state.newPropertyModel} Records`,
            res_model: technicalModel,
            domain: domain,
            context: context,
            views: [[false, "list"], [false, "form"]],
            target: "new",
        });
    }

    onDomainMatchTypeChange(ev) {
        this.state.domainMatchType = ev.target.value;
        this._fetchDomainRecordCount();
    }

    onDomainIncludeArchivedChange(ev) {
        this.state.domainIncludeArchived = ev.target.checked;
        this._fetchDomainRecordCount();
    }

    getDomainOperators() {
        return [
            { value: "=", label: "is equal to" },
            { value: "!=", label: "is not equal to" },
            { value: "<", label: "is less than" },
            { value: "<=", label: "is less than or equal to" },
            { value: ">", label: "is greater than" },
            { value: ">=", label: "is greater than or equal to" },
            { value: "like", label: "contains" },
            { value: "not like", label: "does not contain" },
            { value: "in", label: "is in" },
            { value: "not in", label: "is not in" },
        ];
    }

    getFieldTypes() {
        return [
            { name: "Text", icon: "Ab" },
            { name: "Multiline Text", icon: "≡" },
            { name: "HTML", icon: "</>" },
            { name: "Checkbox", icon: "☑" },
            { name: "Integer", icon: "N°" },
            { name: "Decimal", icon: "1.5" },
            { name: "Monetary", icon: "€" },
            { name: "Date", icon: "📅" },
            { name: "Date & Time", icon: "📆" },
            { name: "Selection", icon: "▼" },
            { name: "Tags", icon: "🏷" },
            { name: "Many2one", icon: "⇥" },
            { name: "Many2many", icon: "⇿" },
            { name: "Signature", icon: "✍" },
            { name: "Separator", icon: "—" },
        ];
    }

    getFieldTypeIcon(typeName) {
        const type = this.getFieldTypes().find(t => t.name === typeName);
        return type ? type.icon : "Ab";
    }

    onTogglePropertiesPanel() {
        this.state.showPropertiesPanel = !this.state.showPropertiesPanel;
    }

    getRelativeTime(dateString) {
        if (!dateString) return "";
        const date = new Date(dateString + "Z");
        const now = new Date();
        const diffMs = now - date;
        const diffMins = Math.floor(diffMs / 60000);
        if (diffMins < 1) return "Just now";
        if (diffMins < 60) return `${diffMins} minutes ago`;
        const diffHours = Math.floor(diffMins / 60);
        if (diffHours < 24) return `${diffHours} hours ago`;
        const diffDays = Math.floor(diffHours / 24);
        return `${diffDays} days ago`;
    }

    async onNewArticle() {
        try {
            if (this.state.isSharedUser) {
                const res = await this.orm.call("info.hub.article", "create_shared_user_private_article", []);
                await this._loadData(true);
                await this.selectArticle(res);
                return;
            }

            const res = await this.orm.create("info.hub.article", [{
                name: "Untitled",
                category: "private",
                body: "",
            }]);
            const newId = Array.isArray(res) ? res[0] : res;

            this.newArticleCreated = true;
            await this._loadData(true);
            await this.selectArticle(newId);
        } catch {
            this.notification.add("Could not create new article.", { type: "danger" });
        }
    }

    async onNewArticleInCurrentSection() {
        try {
            if (this.state.isSharedUser) {
                const res = await this.orm.call("info.hub.article", "create_shared_user_private_article", []);
                await this._loadData(true);
                await this.selectArticle(res);
                return;
            }

            const currentCategory = this.state.activeArticle ? this.state.activeArticle.category : "private";

            const res = await this.orm.create("info.hub.article", [{
                name: "Untitled",
                category: currentCategory,
                body: "",
            }]);
            const newId = Array.isArray(res) ? res[0] : res;

            this.newArticleCreated = true;
            await this._loadData(true);
            await this.selectArticle(newId);
        } catch {
            this.notification.add("Could not create new article.", { type: "danger" });
        }
    }

    async onNewArticleInSection(category) {
        try {
            if (this.state.isSharedUser) {
                if (category === "private") {
                    await this.onNewArticle();
                }
                return;
            }
            const res = await this.orm.create("info.hub.article", [{
                name: "Untitled",
                category: category,
                body: "",
            }]);
            const newId = Array.isArray(res) ? res[0] : res;

            this.newArticleCreated = true;
            await this._loadData(true);
            await this.selectArticle(newId);
        } catch {
            this.notification.add("Could not create article.", { type: "danger" });
        }
    }

    async onNewChildArticle(parentId, ev) {
        try {
            const parentArt = this.state.articles.find((a) => a.id === parentId);
            if (!parentArt) return;

            const category = parentArt.category;

            const res = await this.orm.create("info.hub.article", [{
                name: "Untitled",
                category: category,
                parent_id: parentId,
                body: "",
            }]);
            const newId = Array.isArray(res) ? res[0] : res;

            this.newArticleCreated = true;
            await this._loadData(true);
            await this.selectArticle(newId);
        } catch {
            this.notification.add("Could not create child article.", { type: "danger" });
        }
    }

    async onTitleChange(ev) {
        const newTitle = ev.target.value.trim() || "Untitled";
        if (!this.state.activeArticleId) return;

        try {
            await this.orm.write("info.hub.article", [this.state.activeArticleId], {
                name: newTitle,
            });
            this.state.activeArticle.name = newTitle;
            const localArt = this.state.articles.find((a) => a.id === this.state.activeArticleId);
            if (localArt) localArt.name = newTitle;
            if (this.state.isSharedUser) {
                const sharedArt = this.state.sharedArticles.find((a) => a.id === this.state.activeArticleId);
                if (sharedArt) sharedArt.name = newTitle;
                const privateArt = this.state.privateArticles.find((a) => a.id === this.state.activeArticleId);
                if (privateArt) privateArt.name = newTitle;
            }
            window.dispatchEvent(
                new CustomEvent("info-article-item-changed", {
                    detail: { source: "article_title_rename" }
                })
            );
        } catch {
            this.notification.add("Failed to save title.", { type: "danger" });
        }
    }

    onTitleKeydown(ev) {
        if (ev.key === "Enter") {
            ev.preventDefault();
            this.onTitleChange(ev);
            if (this.editor && this.editor.editable) {
                const el = this.editor.editable;
                el.focus();
                const doc = el.ownerDocument;
                const win = doc.defaultView || window;
                const selection = win.getSelection();
                if (selection) {
                    const range = doc.createRange();
                    let firstChild = el.firstElementChild || el;
                    range.selectNodeContents(firstChild);
                    range.collapse(true);
                    selection.removeAllRanges();
                    selection.addRange(range);
                }
            }
        }
    }

    insertKanbanBlock() {
        if (!this.editor) return;
        const el = this.editor.editable;
        if (!el) return;
        const doc = el.ownerDocument;
        const win = doc.defaultView || window;
        const selection = win.getSelection();

        let range = this.state.slashMenuRange || (selection && selection.rangeCount > 0 ? selection.getRangeAt(0) : null);
        if (!range) return;

        const currentPara = range.startContainer.nodeType === Node.TEXT_NODE
            ? range.startContainer.parentElement.closest("p, div, h1, h2, h3, h4, h5, h6, li")
            : range.startContainer.closest ? range.startContainer.closest("p, div, h1, h2, h3, h4, h5, h6, li") : null;

        const kanbanBlock = doc.createElement("div");
        kanbanBlock.setAttribute("data-embedded", "kanban");
        kanbanBlock.setAttribute("contenteditable", "false");
        kanbanBlock.className = "o_info_kanban_block border rounded p-3 my-3 bg-light";
        kanbanBlock.style.userSelect = "none";
        kanbanBlock.innerHTML = `
            <div class="d-flex align-items-center justify-content-between mb-3 border-bottom pb-2">
                <h5 class="m-0 text-dark"><i class="fa fa-th-large text-primary me-2"></i>Kanban Board</h5>
                <span class="badge bg-secondary bg-opacity-25 text-dark">Kanban Block</span>
            </div>
            <div class="row text-start text-dark">
                <div class="col-4 border-end">
                    <div class="fw-bold mb-2 text-muted text-uppercase small">New</div>
                    <div class="bg-white p-2 rounded shadow-sm mb-2 border">Example Task 1</div>
                    <div class="bg-white p-2 rounded shadow-sm mb-2 border">Example Task 2</div>
                </div>
                <div class="col-4 border-end">
                    <div class="fw-bold mb-2 text-muted text-uppercase small">Ongoing</div>
                    <div class="bg-white p-2 rounded shadow-sm mb-2 border">In Progress Task</div>
                </div>
                <div class="col-4">
                    <div class="fw-bold mb-2 text-muted text-uppercase small">Done</div>
                    <div class="bg-white p-2 rounded shadow-sm mb-2 border-dashed text-muted text-center py-1">No items</div>
                </div>
            </div>
        `;

        const trailingPara = doc.createElement("p");
        trailingPara.innerHTML = "<br>";

        if (currentPara) {
            currentPara.replaceWith(kanbanBlock);
            kanbanBlock.after(trailingPara);
        } else {
            el.appendChild(kanbanBlock);
            el.appendChild(trailingPara);
        }

        const newRange = doc.createRange();
        newRange.setStart(trailingPara, 0);
        newRange.setEnd(trailingPara, 0);
        selection.removeAllRanges();
        selection.addRange(newRange);

        this.state.showSlashMenu = false;
        if (this.editor.shared?.history?.addStep) {
            this.editor.shared.history.addStep();
        }
        this.editor.config.onChange?.();
    }

    onEditorLoad(editor) {
        this.editor = editor;
        setTimeout(() => {
            const el = editor.editable;
            if (el) {
                const doc = el.ownerDocument;
                const win = doc.defaultView || window;

                const enforceTitleBlock = () => {
                    const firstBlock = el.firstElementChild;
                    if (!firstBlock || firstBlock.tagName !== "H1") {
                        if (firstBlock && ["P", "DIV", "H2", "H3", "H4", "H5", "H6"].includes(firstBlock.tagName)) {
                            const h1 = doc.createElement("h1");
                            h1.innerHTML = firstBlock.innerHTML;
                            firstBlock.replaceWith(h1);
                        } else {
                            const h1 = doc.createElement("h1");
                            h1.innerHTML = "<br>";
                            el.insertBefore(h1, el.firstChild);
                        }
                    }
                };

                enforceTitleBlock();
                this._ensureTrailingParagraph(el);

                el.addEventListener("input", () => {
                    this.state.editorDirty = true;
                    enforceTitleBlock();
                    const firstH1 = el.querySelector("h1");
                    if (firstH1) {
                        const titleContent = firstH1.textContent.trim() || "Untitled";
                        if (this.state.activeArticle.name !== titleContent) {
                            this.state.activeArticle.name = titleContent;
                            const localArt = this.state.articles.find((a) => a.id === this.state.activeArticleId);
                            if (localArt) {
                                localArt.name = titleContent;
                                this.state.articles = [...this.state.articles];
                            }
                            if (this.state.isSharedUser) {
                                const sharedArt = this.state.sharedArticles.find((a) => a.id === this.state.activeArticleId);
                                if (sharedArt) {
                                    sharedArt.name = titleContent;
                                    this.state.sharedArticles = [...this.state.sharedArticles];
                                }
                                const privateArt = this.state.privateArticles.find((a) => a.id === this.state.activeArticleId);
                                if (privateArt) {
                                    privateArt.name = titleContent;
                                    this.state.privateArticles = [...this.state.privateArticles];
                                }
                            }
                        }
                    }
                });

                el.addEventListener("keydown", (ev) => {
                    if (ev.key === "Enter") {
                        if (this.state.showEditorHelper) {
                            this.state.showEditorHelper = false;
                        }
                        const selection = win.getSelection();
                        if (selection && selection.rangeCount > 0) {
                            const range = selection.getRangeAt(0);
                            let targetNode = range.startContainer;
                            let targetOffset = range.startOffset;

                            let selectedBlock = null;
                            if (!range.collapsed) {
                                const fragment = range.cloneContents();
                                if (fragment.children.length === 1 && (fragment.children[0].tagName === "IMG" || fragment.children[0].getAttribute("contenteditable") === "false" || fragment.children[0].hasAttribute("data-embedded"))) {
                                    selectedBlock = range.startContainer.childNodes[range.startOffset];
                                } else if (range.startContainer.tagName === "IMG" || range.startContainer.getAttribute("contenteditable") === "false" || range.startContainer.hasAttribute("data-embedded")) {
                                    selectedBlock = range.startContainer;
                                }
                            } else {
                                if (targetNode.nodeType === Node.ELEMENT_NODE) {
                                    const prevNode = targetNode.childNodes[targetOffset - 1];
                                    if (prevNode && (prevNode.tagName === "IMG" || prevNode.getAttribute("contenteditable") === "false" || prevNode.hasAttribute("data-embedded"))) {
                                        selectedBlock = prevNode;
                                    }
                                } else if (targetNode.nodeType === Node.TEXT_NODE) {
                                    if (targetOffset === 0) {
                                        const prevNode = targetNode.previousSibling;
                                        if (prevNode && (prevNode.tagName === "IMG" || (prevNode.nodeType === Node.ELEMENT_NODE && (prevNode.getAttribute("contenteditable") === "false" || prevNode.hasAttribute("data-embedded"))))) {
                                            selectedBlock = prevNode;
                                        }
                                    }
                                }
                            }

                            if (selectedBlock) {
                                ev.preventDefault();
                                ev.stopPropagation();

                                const block = selectedBlock.closest("p, div, h1, h2, h3, h4, h5, h6, li") || selectedBlock.parentElement || selectedBlock;
                                const newPara = doc.createElement("p");
                                newPara.innerHTML = "<br>";

                                if (block === selectedBlock) {
                                    selectedBlock.after(newPara);
                                } else {
                                    block.after(newPara);
                                }

                                const newRange = doc.createRange();
                                newRange.setStart(newPara, 0);
                                newRange.setEnd(newPara, 0);
                                selection.removeAllRanges();
                                selection.addRange(newRange);

                                 if (editor.shared?.history?.addStep) {
                                     editor.shared.history.addStep();
                                 }
                                 editor.config.onChange?.();
                            }
                        }
                    } else if (ev.key === "Backspace") {
                        const sel = win.getSelection();
                        if (!sel || sel.rangeCount === 0 || !sel.isCollapsed) return;

                        const range = sel.getRangeAt(0);

                        const getContainerBlock = (node, editable) => {
                            if (!node) return null;
                            if (node === editable) {
                                return editable.childNodes[range.startOffset] || null;
                            }
                            let current = node.nodeType === Node.TEXT_NODE ? node.parentElement : node;
                            while (current && current.parentElement !== editable) {
                                current = current.parentElement;
                            }
                            return current;
                        };

                        const isCursorAtBlockStart = (node, offset) => {
                            if (node === el) return offset === 0;
                            if (node.nodeType === Node.TEXT_NODE) {
                                if (offset !== 0) return false;
                                let prev = node.previousSibling;
                                while (prev) {
                                    const isBr = prev.nodeName === "BR";
                                    const hasText = prev.textContent.trim().length > 0;
                                    if (!isBr && hasText) return false;
                                    prev = prev.previousSibling;
                                }
                                return true;
                            }
                            if (node.nodeType === Node.ELEMENT_NODE && offset === 0) return true;
                            return false;
                        };

                        const isStart = isCursorAtBlockStart(range.startContainer, range.startOffset);
                        if (!isStart) return;

                        const containerBlock = getContainerBlock(range.startContainer, el);
                        if (!containerBlock) return;

                        const isEmptyBlock = containerBlock.textContent.trim() === "" || containerBlock.innerHTML.trim() === "<br>";

                        const prevBlock = containerBlock.previousElementSibling;
                        const isKanbanBlock = prevBlock && (
                            prevBlock.getAttribute("contenteditable") === "false" ||
                            prevBlock.hasAttribute("data-embedded") ||
                            prevBlock.classList.contains("o_info_kanban_block")
                        );

                        if (prevBlock && isKanbanBlock && (isEmptyBlock || containerBlock === el.childNodes[range.startOffset])) {
                            ev.preventDefault();
                            ev.stopPropagation();

                            prevBlock.remove();

                            let targetPara = containerBlock;
                            if (!el.contains(targetPara)) {
                                targetPara = doc.createElement("p");
                                targetPara.innerHTML = "<br>";
                                el.appendChild(targetPara);
                            }

                            const newRange = doc.createRange();
                            try {
                                newRange.setStart(targetPara, 0);
                                newRange.setEnd(targetPara, 0);
                            } catch {
                                newRange.setStart(el, 0);
                                newRange.setEnd(el, 0);
                            }
                            sel.removeAllRanges();
                            sel.addRange(newRange);

                             if (editor.shared?.history?.addStep) {
                                 editor.shared.history.addStep();
                             }
                             editor.config.onChange?.();
                        }
                    }
                }, true);
                this.updateTOCState();
            }
        }, 0);
        requestAnimationFrame(() => this._applyLockState());

    }

    _applyLockState() {
    if (!this.editor || !this.editor.editable) return;
    const el = this.editor.editable;
    el.setAttribute("contenteditable", this.state.isLocked ? "false" : "true");
}

    _ensureTrailingParagraph(el) {
        if (!el) return;
        const lastChild = el.lastElementChild;
        if (!lastChild) return;

        const isImg = lastChild.tagName === "IMG";
        const containsImgAsLast = lastChild.lastElementChild && lastChild.lastElementChild.tagName === "IMG";
        const isEmbedded = lastChild.getAttribute("contenteditable") === "false" || lastChild.hasAttribute("data-embedded");

        if (isImg || containsImgAsLast || isEmbedded) {
            const p = el.ownerDocument.createElement("p");
            p.innerHTML = "<br>";
            el.appendChild(p);
        }
    }

    _cleanBodyForSave(htmlString) {
        if (!htmlString) return "";
        const parser = new DOMParser();
        const doc = parser.parseFromString(htmlString, "text/html");
        doc.body.querySelectorAll("[data-embedded]").forEach((el) => {
            el.innerHTML = "";
        });
        return doc.body.innerHTML;
    }

    async onEditorBlur() {
        if (!this.editor) return;
        if (!this.state.activeArticleId) return;
        if (this.state.activeArticle.user_permission === 'read') return;
        const el = this.editor.editable || this.editor.getElContent?.();
        if (!el) return;
        this._ensureTrailingParagraph(el);
        const bodyContent = this._cleanBodyForSave(el.innerHTML);
        const currentBodyCleaned = this._cleanBodyForSave(this.state.activeArticle.body);
        if (!this.state.activeArticleId || bodyContent === currentBodyCleaned) return;

        try {
            await this.orm.write("info.hub.article", [this.state.activeArticleId], {
                body: bodyContent,
            });
            this.state.activeArticle.body = bodyContent;
            this.state.activeArticle.bodyMarkup = markup(bodyContent);
            this._originalBody = bodyContent;
            if (this.state.isSharedUser) {
                const sharedArt = this.state.sharedArticles.find((a) => a.id === this.state.activeArticleId);
                if (sharedArt) sharedArt.body = bodyContent;
                const privateArt = this.state.privateArticles.find((a) => a.id === this.state.activeArticleId);
                if (privateArt) privateArt.body = bodyContent;
            }
        } catch {
        }
    }

    getEditorContent() {
        let body = this.state.activeArticle?.body || "";
        const name = this.state.activeArticle?.name || "Untitled";

        const parser = new DOMParser();
        const doc = parser.parseFromString(body, "text/html");
        const firstBlock = doc.body.firstElementChild;
        if (!firstBlock || firstBlock.tagName !== "H1") {
            const h1 = doc.createElement("h1");
            h1.textContent = name;
            doc.body.insertBefore(h1, doc.body.firstChild);
            body = doc.body.innerHTML;
        } else {
            if (firstBlock.textContent.trim() !== name) {
                firstBlock.textContent = name;
                body = doc.body.innerHTML;
            }
        }
        return markup(body);
    }

    getEmbeddings() {
        const infoListEmbedding = {
            name: "info_list",
            Component: EmbeddedListViewComponent,
            getProps: (host) => {
                let props = {};
                try {
                    props = JSON.parse(host.dataset.embeddedProps || "{}");
                } catch (e) {
                    console.error(e);
                }
                return { host, ...props };
            },
        };

        const infoCalendarEmbedding = {
            name: "info_calendar",
            Component: EmbeddedCalendarViewComponent,
            getProps: (host) => {
                let props = {};
                try {
                    props = JSON.parse(host.dataset.embeddedProps || "{}");
                } catch (e) {
                    console.error(e);
                }
                return { host, ...props };
            },
        };

        return [...MAIN_EMBEDDINGS, kanbanEmbedding, infoCardEmbedding, infoListEmbedding, infoCalendarEmbedding];
    }

    getReadonlyEditorConfig() {
        return {
            value: this.state.activeArticle?.bodyMarkup || "",
            embeddedComponents: this.getEmbeddings(),
            hasFullHtml: false,
        };
    }

    getEditorConfig() {

        return {
            content: this.getEditorContent(),
            onClickArticle: this.selectArticle.bind(this),
            Plugins: [
                ...MAIN_PLUGINS,
                ...EMBEDDED_COMPONENT_PLUGINS,
                KanbanPlugin,
                FoldableSectionPlugin,
                ClipboardPluginCommunity,
                ArticlePluginCommunity,
                InformationListPlugin,
                InformationCalendarPlugin,
            ],
            embeddedComponentInfo: {
                app: this.__owl__.app,
                env: this.env,
            },
            resources: {
                embedded_components: this.getEmbeddings(),
            },
            getRecordInfo: () => {
                return {
                    resModel: "info.hub.article",
                    resId: this.state.activeArticleId || null,
                    data: {
                        name: this.state.activeArticle?.name || "",
                        body: this.state.activeArticle?.body || "",
                    },
                    fields: {},
                    id: this.state.activeArticleId || null,
                };
            },
            onChange: () => {
                if (this.state.isLocked) return;
                this.state.showEditorHelper = false;
                const helpers = document.querySelector(".o_info_hub_helpers_wrapper");
                if (helpers) {
                    helpers.style.display = "none";
                }
                if (this.editor) {
                    const el = this.editor.editable || this.editor.getElContent?.();
                    if (el) {
                        this._ensureTrailingParagraph(el);
                        const bodyContent = this._cleanBodyForSave(el.innerHTML);
                        if (bodyContent !== this._cleanBodyForSave(this._originalBody)) {
                            this.state.editorDirty = true;
                        }
                    }
                }
                this.updateTOCState();
            }
        };
    }

    async saveChanges() {
        if (!this.state.activeArticleId) return;

        let bodyContent = this.state.activeArticle.body || "";
        if (this.editor) {
            const el = this.editor.editable || this.editor.getElContent?.();
            if (el) {
                bodyContent = this._cleanBodyForSave(el.innerHTML);
            }
        }

        const parser = new DOMParser();
        const doc = parser.parseFromString(bodyContent, "text/html");
        const firstH1 = doc.body.querySelector("h1");
        let titleContent = "Untitled";
        if (firstH1) {
            titleContent = firstH1.textContent.trim() || "Untitled";
        }

        try {
            await this.orm.write("info.hub.article", [this.state.activeArticleId], {
                name: titleContent,
                body: bodyContent,
            });
            this._originalName = titleContent;
            this._originalBody = bodyContent;
            this.state.activeArticle.name = titleContent;
            this.state.activeArticle.body = bodyContent;
            this.state.activeArticle.bodyMarkup = markup(bodyContent);
            this.state.editorDirty = false;
            this._persistCurrentArticlePropertyValues();
            await this._updateLastEditedMeta();

            const parentId = this.state.activeArticle.parent_id ? (Array.isArray(this.state.activeArticle.parent_id) ? this.state.activeArticle.parent_id[0] : this.state.activeArticle.parent_id) : null;
            this._originalParentPropertyDefs = parentId ? JSON.parse(JSON.stringify(this.state.parentPropertyMap[parentId] || [])) : [];
            this._originalArticlePropertyValues = JSON.parse(JSON.stringify(this.state.articlePropertyValues[this.state.activeArticleId] || {}));

            const localArt = this.state.articles.find((a) => a.id === this.state.activeArticleId);
            if (localArt) {
                localArt.name = titleContent;
                this.state.articles = [...this.state.articles];
            }
            if (this.state.isSharedUser) {
                const sharedArt = this.state.sharedArticles.find((a) => a.id === this.state.activeArticleId);
                if (sharedArt) {
                    sharedArt.name = titleContent;
                    this.state.sharedArticles = [...this.state.sharedArticles];
                }
                const privateArt = this.state.privateArticles.find((a) => a.id === this.state.activeArticleId);
                if (privateArt) {
                    privateArt.name = titleContent;
                    this.state.privateArticles = [...this.state.privateArticles];
                }
            }
        } catch (err) {
            console.error("saveChanges error:", err);
            this.notification.add("Failed to save changes.", { type: "danger" });
        }
    }

    async _restorePropertiesFromBackup() {
        const articleId = this.state.activeArticleId;
        const activeArticle = this.state.activeArticle;
        if (!articleId || !activeArticle) return;
        const parentId = activeArticle.parent_id
            ? (Array.isArray(activeArticle.parent_id) ? activeArticle.parent_id[0] : activeArticle.parent_id)
            : null;
        if (parentId) {
            this.state.parentPropertyMap[parentId] = this._originalParentPropertyDefs ? JSON.parse(JSON.stringify(this._originalParentPropertyDefs)) : [];
        }
        this.state.articlePropertyValues[articleId] = this._originalArticlePropertyValues ? JSON.parse(JSON.stringify(this._originalArticlePropertyValues)) : {};
        
        // Write the original values back to the backend
        const defs = parentId ? (this.state.parentPropertyMap[parentId] || []) : [];
        const values = this.state.articlePropertyValues[articleId] || {};
        try {
            await this.orm.call(
                'info.hub.article',
                'save_article_properties',
                [articleId, parentId, defs, values]
            );
        } catch {}
        
        await this._loadPropertiesForArticle(articleId, parentId);
    }

    async discardChanges() {
        if (!this.state.activeArticleId) return;

        this.state.activeArticle.name = this._originalName;
        this.state.activeArticle.body = this._originalBody;
        this.state.activeArticle.bodyMarkup = this._originalBody ? markup(this._originalBody) : "";

        const localArt = this.state.articles.find((a) => a.id === this.state.activeArticleId);
        if (localArt) localArt.name = this._originalName;

        // Restore properties from session backup
        await this._restorePropertiesFromBackup();

        this.state.editorDirty = false;
        this.state.editorKey += 1;
    }

    async archiveActiveArticle() {
        if (!this.state.activeArticleId) return;

        try {
            await this.orm.call("info.hub.article", "action_archive", [[this.state.activeArticleId]]);

            this.state.activeArticleId = null;
            this.state.activeArticle = null;
            router.pushState({ article_id: undefined, active_id: undefined, id: undefined });

            // Pass goToHome=true so that we show the welcome page instead of the trashed article.
            await this._loadData(false, true);
        } catch {
            this.notification.add("Failed to move article to trash.", { type: "danger" });
        }
    }

    async restoreActiveArticle() {
        if (!this.state.activeArticleId) return;
        const articleId = this.state.activeArticleId;
        try {
            await this.orm.call("info.hub.article", "action_unarchive", [[articleId]]);
            // Reload sidebar data without auto-selection (skipAutoSelect=true)
            // so the restored article appears in sidebar
            await this._loadData(true);
            // Now open the article — it's active again and will render normally
            await this.selectArticle(articleId, true, true);
        } catch {
            this.notification.add("Failed to restore article.", { type: "danger" });
        }
    }

    async openTrash() {
        this.action.doAction("info_hub.action_info_article_trash");
    }

    toggleSidebar() {
        this.state.isSidebarOpen = !this.state.isSidebarOpen;
    }

    async toggleFavorite() {
        if (!this.state.activeArticleId) return;
        const newFav = !this.state.favorited;
        try {
            await this.orm.write("info.hub.article", [this.state.activeArticleId], {
                is_favorite: newFav,
            });
            this.state.favorited = newFav;
            const activeArt = this.state.articles.find((a) => a.id === this.state.activeArticleId);
            if (activeArt) activeArt.is_favorite = newFav;

            if (this.state.isSharedUser) {
                const sharedArt = this.state.sharedArticles.find((a) => a.id === this.state.activeArticleId);
                if (sharedArt) sharedArt.is_favorite = newFav;
                const privateArt = this.state.privateArticles.find((a) => a.id === this.state.activeArticleId);
                if (privateArt) privateArt.is_favorite = newFav;

                if (newFav) {
                    const artObj = sharedArt || privateArt;
                    if (artObj && !this.state.favoritedArticles.some((a) => a.id === artObj.id)) {
                        this.state.favoritedArticles.push(artObj);
                    }
                } else {
                    this.state.favoritedArticles = this.state.favoritedArticles.filter((a) => a.id !== this.state.activeArticleId);
                }
            }
        } catch {
        }
    }
    onClickChat() {
        this.state.showChatter = !this.state.showChatter;
        if (this.state.showChatter && this.state.showTOCPanel) {
            this.state.showTOCPanel = false;
        }
    }

    getArticleBodyEl() {
        if (!this.state.activeArticle) {
            return null;
        }
        if (this.state.activeArticle.user_permission === 'read') {
            return document.querySelector(".o_info_hub_read_only_body");
        } else {
            return this.editor?.editable || document.querySelector(".o_info_hub_editor_body");
        }
    }

    _detectHeadingsFromBody(htmlString) {
        if (!htmlString) {
            this.state.hasHeadings = false;
            return;
        }
        try {
            const parser = new DOMParser();
            const doc = parser.parseFromString(htmlString, "text/html");
            const headings = doc.querySelectorAll("h1, h2, h3, h4, h5, h6");

            let hasValidHeading = false;
            for (const h of headings) {
                const text = h.textContent.trim().toLowerCase();
                if (text.replaceAll("\u200B", "").length > 0 && text !== "untitled" && text !== "untitled article") {
                    hasValidHeading = true;
                    break;
                }
            }
            this.state.hasHeadings = hasValidHeading;
            if (!hasValidHeading && this.state.showTOCPanel) {
                this.state.showTOCPanel = false;
            }
        } catch (e) {
            this.state.hasHeadings = false;
        }
    }

    updateTOCState() {
        const bodyEl = this.getArticleBodyEl();
        if (!bodyEl) {
            this._detectHeadingsFromBody(this.state.activeArticle?.body);
            return;
        }

        const validHeadings = this.tocManager.fetchValidHeadings(bodyEl).filter(h => {
            const text = h.innerText ? h.innerText.trim().toLowerCase() : "";
            return text.replaceAll("\u200B", "").length > 0 && text !== "untitled" && text !== "untitled article";
        });
        const hasHeadings = validHeadings.length > 0;
        this.state.hasHeadings = hasHeadings;

        if (!hasHeadings && this.state.showTOCPanel) {
            this.state.showTOCPanel = false;
        }

        if (this.state.showTOCPanel) {
            this.tocManager.updateStructure();
        }
    }

    shouldShowTOCButton() {
        return this.state.hasHeadings;
    }

    onToggleTOCPanel() {
        this.state.showTOCPanel = !this.state.showTOCPanel;
        if (this.state.showTOCPanel && this.state.showChatter) {
            this.state.showChatter = false;
        }
        if (this.state.showTOCPanel) {
            this.updateTOCState();
        }
    }

    async onRemoveIcon() {
        if (!this.state.activeArticleId) return;
        try {
            await this.orm.write("info.hub.article", [this.state.activeArticleId], { icon: "📄" });
            this.state.activeArticle.icon = "📄";
            const localArt = this.state.articles.find((a) => a.id === this.state.activeArticleId);
            if (localArt) localArt.icon = "📄";
        } catch {
            this.notification.add("Failed to remove icon.", { type: "danger" });
        }
    }

    async onAddRandomIcon() {
        if (!this.state.activeArticleId) return;

        const emojis = [
            "😀", "😃", "😄", "😁", "😆", "😅", "😂", "🤣", "😊", "😇",
            "🙂", "🙃", "😉", "😌", "😍", "🥰", "😘", "😗", "😙", "😚",
            "😋", "😛", "😝", "😜", "🤪", "🤨", "🧐", "🤓", "😎", "🤩",
            "🥳", "😏", "😒", "😞", "😔", "😟", "😕", "🙁", "☹️", "😣",
            "😖", "😫", "😩", "🥺", "😢", "😭", "😤", "😠", "😡", 
            "🤯", "😳", "🥵", "🥶", "😱", "😨", "😰", "😥", "😓", "🤗",
            "🤔", "🤭", "🤫", "🤥", "😶", "😐", "😑", "😬", "🙄", "😯",
            "😦", "😧", "😮", "😲", "🥱", "😴", "🤤", "😪", "😵", "🤐",
             "😷", "🤒", "🤕", "🤑", "🤠", "😈",
            , "👻", "💀", "☠️", "👽", "👾",
            "🤖", "🎃", "🍉", "🍊", "🍋", "🍌", "🍍", "🍎", "🍏", "🍐",
            "🍑", "🍒", "🍓", "🫐", "🥝", "🍅", "🥑", "🍆", "🥔", "🥕",
            "🌽", "🌶️", "🥬", "🥦", "🍄", "🥨", "🥞", "🧇", "🧀", "🍖",
            "🌭", "🍔", "🍟", "🍕", "🥪", "🍳", "🍲", "🍿", "🍩", "🍪",
            "🎂", "🧁", "🍫", "🍬", "🍭", "⚽️", "🏀", "🏈", "⚾️", "🥎",
            "🎾", "🏐", "🏉", "🎱", "🪀", "🏓", "🏸", "🥅", "🛹", "🛼",
            "🚲", "🏍️", "🏎️", "✈️", "🚢", "🚗", "🚕", "🚙", "🚌", "🚎"
        ];
        const randomEmoji = emojis[Math.floor(Math.random() * emojis.length)];
        try {
            await this.orm.write("info.hub.article", [this.state.activeArticleId], { icon: randomEmoji });
            this.state.activeArticle.icon = randomEmoji;
            const localArt = this.state.articles.find((a) => a.id === this.state.activeArticleId);
            if (localArt) localArt.icon = randomEmoji;
            await this._updateLastEditedMeta();

            // Close emoji picker if it was open
            this.state.showEmojiPicker = false;
        } catch (err) {
            console.error("Failed to set random icon:", err);
            this.notification.add("Failed to add random icon.", { type: "danger" });
        }
    }

    onToggleEmojiPicker() {
        if (!this.state.activeArticleId) return;
        this.state.showEmojiPicker = !this.state.showEmojiPicker;

        this.state.showCoverUpload = false;
        this.state.showVersionHistory = false;
        this.state.showMoveToDialog = false;
    }

    async onSelectEmoji(emoji) {
        if (!this.state.activeArticleId) return;
        try {
            await this.orm.write("info.hub.article", [this.state.activeArticleId], { icon: emoji });
            this.state.activeArticle.icon = emoji;
            const localArt = this.state.articles.find((a) => a.id === this.state.activeArticleId);
            if (localArt) localArt.icon = emoji;
            this.state.showEmojiPicker = false;
        } catch {
            this.notification.add("Failed to update icon.", { type: "danger" });
        }
    }

    onEmojiSearch(ev) {
        this.state.emojiSearchQuery = ev.target.value.toLowerCase().trim();
    }

    getEmojiCategories() {
        return [
            { key: "smileys", label: "Smileys & Emotion", icon: "😀" },
            { key: "people", label: "People & Body", icon: "👋" },
            { key: "nature", label: "Animals & Nature", icon: "🐼" },
            { key: "food", label: "Food & Drink", icon: "🍕" },
            { key: "activities", label: "Activities", icon: "⚽" },
            { key: "travel", label: "Travel & Places", icon: "✈️" },
            { key: "objects", label: "Objects", icon: "💼" },
            { key: "symbols", label: "Symbols", icon: "❤️" },
        ];
    }

    _getEmojiData() {
        return {
            smileys: [
                "😀", "😁", "😂", "🤣", "😃", "😄", "😅", "😆", "😇", "😉",
                "😊", "😋", "🤭", "🥰", "😘", "😗", "😙", "😚", "☺️", "🙂",
                "🙃", "🤔", "🤩", "🥳", "😎", "🤓", "🥷", "😕", "😟", "🙁",
                "😮", "😯", "😲", "😳", "🤪", "😷", "🤒", "🤕", "🤢", "🤮",
                "😈", "👿", "👹", "👺", "🤡", "💩", "👻", "💀", "☠️", "👽",
            ],
            people: [
                "👋", "🤚", "👌", "✌️", "🤞", "🤟", "🤘", "👍", "👎", "✊",
                "👊", "🤛", "🤜", "👈", "👉", "👆", "👇", "☝️", "🤣", "👏",
                "🙌", "🤲", "🤳", "💪", "🦵", "🦶", "🤝", "🙏", "✍️", "💅",
                "💁", "💁‍♂️", "🙋", "💆", "💇", "🙇", "🚶", "🏃", "💃", "🕵️",
                "👨", "👩", "👦", "👧", "👶", "👴", "👵", "👱", "👲", "👳",
            ],
            nature: [
                "🐶", "🐱", "🐭", "🐹", "🐰", "🦊", "🐼", "🐻", "🐼", "🐽",
                "👀", "🐮", "🐷", "🐿️", "🦌", "🐵", "🐔", "🦆", "🦅", "🦉",
                "🐸", "🐊", "🐢", "🐍", "🦎", "🦖", "🐳", "🐾", "🌸", "🌹",
                "🌺", "🌻", "🌼", "🌽", "🌾", "🌿", "🍀", "🍁", "🍂", "🍃",
                "🍄", "🍅", "🌱", "🌲", "🌳", "🌴", "🌵", "⛄", "☀️", "🌈",
            ],
            food: [
                "🍕", "🍔", "🍟", "🍗", "🍖", "🌭", "🍳", "🥞", "🍣", "🍱",
                "🍜", "🍲", "🍦", "🍧", "🍨", "🍩", "🍰", "🎂", "🍪", "🍫",
                "🍬", "🍭", "🍮", "🍯", "🥤", "🥙", "🥚", "🥛", "🥜", "🥝",
                "🥖", "🥗", "🥘", "🍎", "🍏", "🍊", "🍋", "🍌", "🍇", "🍉",
                "☕", "🍵", "🍶", "🍷", "🍸", "🍹", "🍺", "🍻", "🥂", "🥃",
            ],
            activities: [
                "⚽", "🎵", "🎮", "🎲", "♟️", "🏆", "🎯", "🥊", "🏅", "🏄",
                "🏈", "🎾", "🎱", "🎳", "🏊", "🏇", "⛷️", "🏆", "🥋", "🥌",
                "🎻", "🏓", "🏉", "🤺", "🏋️", "🤸", "🤼", "🤽", "🤾", "🚴",
                "🎭", "🎨", "🎧", "🎤", "🎸", "🎹", "🎺", "🎻", "🎼", "🎬",
                "🎪", "🎫", "🎠", "🎡", "🎢", "🎣", "🎤", "📷", "🔭", "🔬",
            ],
            travel: [
                "✈️", "🚗", "🚌", "🚂", "🚃", "🚄", "🚅", "🚆", "🚇", "🚈",
                "🚉", "🚝", "🚍", "🚎", "🚑", "🚒", "🚓", "🚕", "🚖", "🚘",
                "🚢", "🚤", "🚥", "🚦", "🚧", "⛽", "🚨", "🚩", "🚪", "🚫",
                "🏛️", "🏔️", "🏕️", "🏖️", "🏗️", "🏘️", "🏙️", "🏚️", "🏜️", "🏝️",
                "🏞️", "🏟️", "🏠", "🏡", "🏢", "🏣", "🏤", "🏥", "🏦", "🏧",
            ],
            objects: [
                "💼", "📄", "📝", "📋", "📁", "📂", "🗂️", "📚", "📖", "📕",
                "📗", "📘", "📙", "🗒️", "🗓️", "📌", "📍", "📎", "✂️", "🖊️",
                "✏️", "🖋️", "🔍", "🔎", "💡", "🔦", "🕧", "📱", "💻", "⌨️",
                "🖥️", "🖨️", "👫", "📷", "📸", "📹", "📺", "📻", "📼", "📡",
                "🔧", "🔨", "🔩", "🔪", "🔑", "🔒", "🔓", "🛠️", "⚙️", "🧰",
            ],
            symbols: [
                "❤️", "💛", "💚", "💙", "💜", "🖤", "♥️", "♦️", "♣️", "♠️",
                "🕎", "✔️", "❌", "❓", "❕", "❗", "⚠️", "🚫", "🔞", "🔄",
                "⬆️", "⬇️", "➡️", "⬅️", "↗️", "↘️", "↙️", "↖️", "↕️", "↔️",
                "⏰", "⏱️", "⏲️", "⏳", "⏸️", "⏹️", "▶️", "⏪", "⏩", "🔀",
                "⭐", "🌟", "⚡", "🔥", "✅", "⚽", "🎯", "🚀", "💎", "🧩",
            ],
        };
    }

    getVisibleEmojis() {
        const data = this._getEmojiData();
        const query = this.state.emojiSearchQuery;

        if (query) {
            const all = Object.values(data).flat();
            return all.filter((e) => e.includes(query) || all.indexOf(e) >= 0);
        }

        return data[this.state.emojiActiveCategory] || data.smileys;
    }

    onAddCover() {
        if (!this.state.activeArticleId) return;
        this.state.showCoverUpload = false;
        this.dialog.add(
            InfoCoverDialog,
            {
                articleId: this.state.activeArticleId,
                currentCover: this.state.activeArticle?.cover_image || false,
                onCoverApplied: async (base64) => {
                    if (this.state.activeArticle) {
                        this.state.activeArticle.cover_image = base64;
                    }
                    await this._updateLastEditedMeta();
                },
            }
        );
    }

    async onCoverFileChange(ev) {
        const file = ev.target.files[0];
        if (!file || !this.state.activeArticleId) return;
        const reader = new FileReader();
        reader.onload = async (e) => {
            const base64Data = e.target.result.split(",")[1];
            try {
                await this.orm.write("info.hub.article", [this.state.activeArticleId], {
                    cover_image: base64Data,
                });
                this.state.activeArticle.cover_image = base64Data;
                this.state.showCoverUpload = false;
                await this._updateLastEditedMeta();
            } catch {
                this.notification.add("Failed to save cover image.", { type: "danger" });
            }
        };
        reader.readAsDataURL(file);
    }

    async onRemoveCover() {
        if (!this.state.activeArticleId) return;
        try {
            await this.orm.call("info.hub.article", "remove_cover_image", [this.state.activeArticleId]);
            this.state.activeArticle.cover_image = false;
            this.state.showCoverUpload = false;
            await this._updateLastEditedMeta();
        } catch {
            this.notification.add("Failed to remove cover image.", { type: "danger" });
        }
    }
    onRepositionCover() {
        this.state.repositioning = false;
        this.state.coverDragStartY = null;
        this.state.coverObjectPosition = this.state.activeArticle?.cover_image_position !== undefined ? this.state.activeArticle.cover_image_position : 50;
        this.state.repositioning = true;
    }

    onCoverDragStart(ev) {
        if (!this.state.repositioning) return;
        ev.preventDefault();
        this.state.coverDragStartY = ev.clientY;
        this.state.isDragging = true;

        this._onWindowMouseMove = (moveEv) => {
            if (this.state.coverDragStartY === null) return;
            const delta = moveEv.clientY - this.state.coverDragStartY;
            this.state.coverDragStartY = moveEv.clientY;
            const newPos = Math.min(100, Math.max(0, this.state.coverObjectPosition - delta * 0.3));
            this.state.coverObjectPosition = newPos;
        };

        this._onWindowMouseUp = () => {
            this.state.coverDragStartY = null;
            this.state.isDragging = false;
            window.removeEventListener("mousemove", this._onWindowMouseMove);
            window.removeEventListener("mouseup", this._onWindowMouseUp);
        };

        window.addEventListener("mousemove", this._onWindowMouseMove);
        window.addEventListener("mouseup", this._onWindowMouseUp);
    }

    onCoverDragMove(ev) {
        // Handled by window level listener for smoother dragging
    }

    onCoverDragEnd() {
        // Handled by window level listener
    }

    async onSaveReposition() {
        await this.orm.write("info.hub.article", [this.state.activeArticleId], {
            cover_image_position: this.state.coverObjectPosition,
        });
        if (this.state.activeArticle) {
            this.state.activeArticle.cover_image_position = this.state.coverObjectPosition;
        }
        this.state.repositioning = false;
        await this._updateLastEditedMeta();
    }

    onCancelReposition() {
        this.state.repositioning = false;
    }

    async onToggleFullWidth() {
        if (!this.state.activeArticleId) return;
        try {
            const newVal = await this.orm.call(
                "info.hub.article", "toggle_full_width", [this.state.activeArticleId]
            );
            this.state.isFullWidth = newVal;
        } catch {
            this.notification.add("Failed to toggle full width.", { type: "danger" });
        }
    }

    async onOpenMoveTo() {
        if (!this.state.activeArticleId) return;
        this.state.moveToArticleId = null;
        this.state.showMoveToDialog = true;
    }

    onMoveToArticleChange(ev) {
        this.state.moveToArticleId = parseInt(ev.target.value) || null;
    }

    async onConfirmMoveTo() {
        if (!this.state.activeArticleId || !this.state.moveToArticleId) return;
        try {
            await this.orm.write(
                "info.hub.article",
                [this.state.activeArticleId],
                { parent_id: this.state.moveToArticleId }
            );
            this.state.showMoveToDialog = false;
            await this._loadData();
            await this.selectArticle(this.state.activeArticleId);
        } catch {
            this.notification.add("Failed to move article.", { type: "danger" });
        }
    }

    onCancelMoveTo() {
        this.state.showMoveToDialog = false;
    }

    async onToggleLock() {
        if (!this.state.activeArticleId) return;
        try {
            const newVal = await this.orm.call(
                "info.hub.article", "toggle_lock", [this.state.activeArticleId]
            );
            this.state.isLocked = newVal;
            this._applyLockState();
        } catch {
            this.notification.add("Failed to toggle lock.", { type: "danger" });
        }
    }



        onRequireReading() {
        if (!this.state.activeArticleId) return;
        this.action.doAction({
            type: "ir.actions.act_window",
            name: "Assign Mandatory Reading",
            res_model: "info.hub.assign.reading.wizard",
            views: [[false, "form"]],
            target: "new",
            context: {
                default_article_id: this.state.activeArticleId,
            },
        }, {
            onClose: async () => {
                await this._loadData();
                await this.selectArticle(this.state.activeArticleId, false);
            }
        });
    }

    async onCreateCopy() {
        if (!this.state.activeArticleId) return;
        try {
            const newId = await this.orm.call(
                "info.hub.article", "duplicate_article", [this.state.activeArticleId]
            );
            await this._loadData();
            await this.selectArticle(newId);
        } catch {
            this.notification.add("Failed to create a copy.", { type: "danger" });
        }
    }

    async onOpenVersionHistory() {
        if (!this.state.activeArticleId) return;
        this.dialog.add(InfoArticleVersionHistoryDialog, {
            articleId: this.state.activeArticleId,
            currentBody: this.state.activeArticle.body || "",
            onRestore: async (restoredBody) => {
                this.state.activeArticle.body = restoredBody;
                this.state.activeArticle.bodyMarkup = markup(restoredBody);
                this.state.editorKey++;
            }
        });
    }

    onDownloadPDF() {
        var printContents = document.getElementById('content_body').innerHTML;
        var originalContents = document.body.innerHTML;

        document.body.innerHTML = printContents;
        window.print();

        document.body.innerHTML = originalContents;
        location.reload();
    }

    async onAddToTemplates() {
        if (!this.state.activeArticleId) return;
        try {
            await this.action.doAction({
                type: "ir.actions.act_window",
                name: _t("Add to Templates"),
                res_model: "info.hub.add.to.template.wizard",
                views: [[false, "form"]],
                target: "new",
                context: {
                    default_article_id: this.state.activeArticleId,
                    active_id: this.state.activeArticleId,
                    active_model: "info.hub.article",
                },
            }, {
                onClose: async () => {
                    await this._loadData();
                },
            });
        } catch {
            this.notification.add(_t("Failed to open Add to Templates."), { type: "danger" });
        }
    }


    onBrowseTemplates() {
        this.dialog.add(BrowseTemplatesDialog, {
            onTemplateSelected: async (newArticleId) => {
                try {
                    await this._loadData();
                    await this.selectArticle(newArticleId);
                } catch (err) {
                    this.notification.add("Created article, but failed to load it automatically.", { type: "danger" });
                }
            }
        });
    }

    onFilterInput(ev) {
        this.state.filterText = ev.target.value;
    }

    onDragStart(ev) {
        const row = ev.currentTarget;
        const articleId = Number(row.dataset.articleId);
        const section = row.dataset.section;

        this._drag.articleId = articleId;
        this._drag.sourceSection = section;
        this._drag.startX = ev.clientX;

        ev.dataTransfer.effectAllowed = "move";
        ev.dataTransfer.setData("text/plain", String(articleId));

        requestAnimationFrame(() => row.classList.add("o_info_hub_dragging"));
    }

    onDragEnd(ev) {
        const row = ev.currentTarget;
        row.classList.remove("o_info_hub_dragging");

        document.querySelectorAll(".o_info_hub_drop_above, .o_info_hub_drop_below, .o_info_hub_drop_target").forEach(
            (el) => el.classList.remove("o_info_hub_drop_above", "o_info_hub_drop_below", "o_info_hub_drop_target")
        );
        document.querySelectorAll(".o_info_hub_section_content.o_info_hub_drag_over").forEach(
            (el) => el.classList.remove("o_info_hub_drag_over")
        );

        this._drag = { articleId: null, sourceSection: null, overEl: null, startX: null, currentX: null };
    }

    // -------------------------------------------------------------------------
    // Property drag-and-drop handlers (reordering custom properties)
    // -------------------------------------------------------------------------
    onPropDragStart(ev) {
        const el = ev.currentTarget;
        const index = Number(el.dataset.index);
        this._propDrag.sourceIndex = index;
        ev.dataTransfer.effectAllowed = "move";
        ev.dataTransfer.setData("text/plain", String(index));
        requestAnimationFrame(() => el.classList.add("o_info_hub_dragging"));
    }

    onPropDragOver(ev) {
        ev.preventDefault();
        ev.dataTransfer.dropEffect = "move";
    }

    onPropDrop(ev) {
        ev.preventDefault();
        const targetEl = ev.currentTarget;
        const targetIndex = Number(targetEl.dataset.index);
        const sourceIndex = this._propDrag.sourceIndex;
        if (sourceIndex === null || sourceIndex === targetIndex) return;

        const rect = targetEl.getBoundingClientRect();
        const middleY = rect.top + rect.height / 2;
        const insertAfter = ev.clientY > middleY;

        const sourceProp = this.state.customProperties[sourceIndex];
        // If dragging a Separator, move the whole section block
        if (sourceProp && sourceProp.type === 'Separator') {
            const props = this.state.customProperties;
            let endIdx = sourceIndex;
            for (let i = sourceIndex + 1; i < props.length; i++) {
                if (props[i].type === 'Separator') {
                    endIdx = i - 1;
                    break;
                }
                endIdx = i;
            }
            const block = props.slice(sourceIndex, endIdx + 1);
            props.splice(sourceIndex, block.length);
            let insertAt = targetIndex;
            if (insertAfter) {
                if (sourceIndex < targetIndex) {
                    insertAt = targetIndex - block.length + 1;
                } else {
                    insertAt = targetIndex + 1;
                }
            } else {
                if (sourceIndex < targetIndex) {
                    insertAt = targetIndex - block.length;
                } else {
                    insertAt = targetIndex;
                }
            }
            insertAt = Math.max(0, Math.min(props.length, insertAt));
            props.splice(insertAt, 0, ...block);
        } else {
            // Normal property move (single item)
            const moved = this.state.customProperties.splice(sourceIndex, 1)[0];
            let insertAt = targetIndex;
            if (insertAfter) {
                if (sourceIndex < targetIndex) {
                    insertAt = targetIndex;
                } else {
                    insertAt = targetIndex + 1;
                }
            } else {
                if (sourceIndex < targetIndex) {
                    insertAt = targetIndex - 1;
                } else {
                    insertAt = targetIndex;
                }
            }
            insertAt = Math.max(0, Math.min(this.state.customProperties.length, insertAt));
            this.state.customProperties.splice(insertAt, 0, moved);
        }
        this.state.customProperties = [...this.state.customProperties];
        this._syncParentPropertyMap();
        this.state.editorDirty = true;
        this._propDrag.sourceIndex = null;
    }

    onPropDragEnd(ev) {
        const el = ev.currentTarget;
        el.classList.remove("o_info_hub_dragging");
        this._propDrag.sourceIndex = null;
    }

    onDragOver(ev) {
        const section = ev.currentTarget;

        if (section.dataset.section === "favorites") {
            ev.preventDefault();
            ev.dataTransfer.dropEffect = "none";
            section.classList.add("o_info_hub_drag_no_drop");
            return;
        }

        ev.preventDefault();
        ev.dataTransfer.dropEffect = "move";

        section.classList.add("o_info_hub_drag_over");

        const rows = [...section.querySelectorAll(".o_info_hub_item_row:not(.o_info_hub_dragging)")];
        let targetRow = null;
        let insertBefore = true;

        for (const row of rows) {
            const rect = row.getBoundingClientRect();
            const midY = rect.top + rect.height / 2;
            if (ev.clientY < midY) {
                targetRow = row;
                insertBefore = true;
                break;
            }
            targetRow = row;
            insertBefore = false;
        }

        rows.forEach((r) => r.classList.remove("o_info_hub_drop_above", "o_info_hub_drop_below"));
        if (targetRow) {
            targetRow.classList.add(insertBefore ? "o_info_hub_drop_above" : "o_info_hub_drop_below");
        }

        this._drag.overEl = targetRow;
        this._drag._insertBefore = insertBefore;
        this._drag.currentX = ev.clientX;
    }

    onDragLeave(ev) {
        const section = ev.currentTarget;
        if (!section.contains(ev.relatedTarget)) {
            section.classList.remove("o_info_hub_drag_over");
            section.querySelectorAll(".o_info_hub_drop_above, .o_info_hub_drop_below").forEach(
                (el) => el.classList.remove("o_info_hub_drop_above", "o_info_hub_drop_below")
            );
        }
    }

    async onDrop(ev) {
        ev.preventDefault();

        const section = ev.currentTarget;
        section.classList.remove("o_info_hub_drag_over");
        section.querySelectorAll(".o_info_hub_drop_above, .o_info_hub_drop_below").forEach(
            (el) => el.classList.remove("o_info_hub_drop_above", "o_info_hub_drop_below")
        );

        if (section.dataset.section === "favorites") return;

        const draggedId = this._drag.articleId;
        if (!draggedId) return;

        const targetEl = this._drag.overEl;
        const insertBefore = this._drag._insertBefore;
        const targetId = targetEl ? Number(targetEl.dataset.articleId) : null;

        if (draggedId === targetId) return;

        const targetCategory = section.dataset.workspaceType;
        const targetSection = section.dataset.section;
        const sourceSection = this._drag.sourceSection;
        const targetWorkspaceType = section.dataset.workspaceType;
        const draggedArticle = this.state.articles.find((a) => a.id === draggedId);

        const currentCategory = draggedArticle ? draggedArticle.category : null;
        const isCrossSection = targetCategory ? (currentCategory !== targetCategory) : (targetSection !== sourceSection);

        if (isCrossSection && targetWorkspaceType === "shared") {
            const memberCount = await this.orm.searchCount("info.hub.article.member", [
                ["article_id", "=", draggedId],
            ]);
            if (memberCount < 2) {
                this.dialog.add(ConfirmationDialog, {
                    title: _t("Warning"),
                    body: _t("You need at least 2 members for the Article to be shared."),
                    confirmLabel: _t("Ok"),
                    cancelLabel: "",
                    confirm: () => {},
                });
                return;
            }
        }

        if (!isCrossSection) {
            await this._executeDrop({
                section,
                draggedId,
                draggedArticle,
                targetCategory,
                targetWorkspaceType,
                targetId,
                insertBefore,
            });
            return;
        }

        const draggedName = draggedArticle ? draggedArticle.name : "this article";

        const sectionNameMap = {
            workspace: "Workspace",
            shared:    "Shared",
            private:   "Private",
        };

        let destinationLabel;
        if (targetWorkspaceType) {
            destinationLabel = sectionNameMap[targetWorkspaceType]
                || targetWorkspaceType.charAt(0).toUpperCase() + targetWorkspaceType.slice(1);
        } else if (targetEl) {
            const targetArticle = this.state.articles.find((a) => a.id === targetId);
            destinationLabel = targetArticle ? `"${targetArticle.name}"` : "the new position";
        } else {
            destinationLabel = "the new position";
        }

        const confirmLabel = targetWorkspaceType
            ? `Move to ${sectionNameMap[targetWorkspaceType] || destinationLabel}`
            : "Move";

        await new Promise((resolve) => {
            this.dialog.add(ConfirmationDialog, {
                title: "Move Article",
                body: `Are you sure you want to move "${draggedName}" to ${destinationLabel}?`,
                confirmLabel,
                cancelLabel: "Cancel",
                confirm: async () => {
                    await this._executeDrop({
                        section,
                        draggedId,
                        draggedArticle,
                        targetCategory,
                        targetWorkspaceType,
                        targetId,
                        insertBefore,
                    });
                    resolve();
                },
                cancel: () => {
                    resolve();
                },
            });
        });
    }

    async _executeDrop({ section, draggedId, draggedArticle, targetCategory, targetWorkspaceType, targetId, insertBefore }) {
        const THRESHOLD = 40;
        const deltaX = (this._drag.currentX ?? this._drag.startX ?? 0) - (this._drag.startX ?? 0);

        if (deltaX > THRESHOLD) {
            const sectionRows = [...section.querySelectorAll(".o_info_hub_item_row")];
            const draggedIdx = sectionRows.findIndex((r) => Number(r.dataset.articleId) === draggedId);
            const newParentRow = sectionRows
                .slice(0, draggedIdx === -1 ? undefined : draggedIdx)
                .reverse()
                .find((r) => Number(r.dataset.articleId) !== draggedId);

            const newParentId = newParentRow ? Number(newParentRow.dataset.articleId) : null;

            const isDescendant = (childId, ancestorId) => {
                const art = this.state.articles.find((a) => a.id === childId);
                if (!art || !art.parent_id) return false;
                const pid = Array.isArray(art.parent_id) ? art.parent_id[0] : art.parent_id;
                if (pid === ancestorId) return true;
                return isDescendant(pid, ancestorId);
            };

            if (isDescendant(newParentId, draggedId)) {
                this.notification.add("Cannot nest an article under its own child.", { type: "warning" });
                return;
            }

            await this.orm.write("info.hub.article", [draggedId], { parent_id: newParentId });

            const localArt = this.state.articles.find((a) => a.id === draggedId);
            if (localArt) localArt.parent_id = [newParentId];

            this.state.articles = [...this.state.articles];
            return;
        }

        if (deltaX < -THRESHOLD) {
            const currentParent = draggedArticle?.parent_id;

            await this.orm.write("info.hub.article", [draggedId], { parent_id: false });

            const localArt = this.state.articles.find((a) => a.id === draggedId);
            if (localArt) localArt.parent_id = false;

            this.state.articles = [...this.state.articles];
            return;
        }
        if (targetCategory && draggedArticle) {
            const currentCategory = draggedArticle.category;
            const isCrossSection = currentCategory !== targetCategory;

            if (isCrossSection) {
                await this.orm.write("info.hub.article", [draggedId], {
                    category: targetCategory,
                });

                const localArt = this.state.articles.find((a) => a.id === draggedId);
                if (localArt) {
                    localArt.category = targetCategory;
                }

            }
        }

        const sectionRows = [...section.querySelectorAll(".o_info_hub_item_row")];
        let orderedIds = sectionRows
            .map((r) => Number(r.dataset.articleId))
            .filter((id) => id && id !== draggedId);

        const insertIdx = targetId
            ? orderedIds.indexOf(targetId) + (insertBefore ? 0 : 1)
            : orderedIds.length;

        orderedIds.splice(insertIdx, 0, draggedId);

        const articlesById = Object.fromEntries(this.state.articles.map((a) => [a.id, a]));
        const reorderedSection = orderedIds.map((id) => articlesById[id]).filter(Boolean);
        const otherArticles = this.state.articles.filter((a) => !orderedIds.includes(a.id));

        reorderedSection.forEach((art, idx) => { art.sequence = (idx + 1) * 10; });

        this.state.articles = [...otherArticles, ...reorderedSection];

        await this._persistSequences(reorderedSection);
    }

    async _persistSequences(articles) {
        try {
            await Promise.all(
                articles.map((art) =>
                    this.orm.write("info.hub.article", [art.id], { sequence: art.sequence })
                )
            );
        } catch {
            this.notification.add("Could not save article order.", { type: "warning" });
        }
    }

    async _loadKanbanStages(articleId) {
        try {
            const stages = await this.orm.searchRead(
                "info.hub.article.stage",
                [["parent_id", "=", articleId]],
                ["id", "name", "sequence"],
                { order: "sequence asc, id asc", context: { active_test: false } }
            );
            this.state.kanbanStages = stages;
        } catch {
            this.state.kanbanStages = [];
        }
    }

    /**
     * Fetch archived article items (active=false) grouped by stage for the
     * read-only Kanban snapshot shown when a Kanban article is in the Trash.
     * Uses orm.searchRead directly with active_test:false so we bypass the
     * View component's unreliable active_test context propagation.
     */
    async _loadArchivedKanbanItems(articleId) {
        try {
            const items = await this.orm.searchRead(
                "info.hub.article",
                [
                    ["parent_id", "=", articleId],
                    ["is_article_item", "=", true],
                ],
                ["id", "name", "icon", "stage_id", "author_id", "cover_image"],
                {
                    order: "sequence asc, id asc",
                    context: { active_test: false },
                }
            );
            // Group items by stage id so the template can render columns easily
            const byStage = {};
            for (const item of items) {
                const sid = item.stage_id ? item.stage_id[0] : 0;
                if (!byStage[sid]) byStage[sid] = [];
                byStage[sid].push(item);
            }
            this.state.archivedKanbanItems = byStage;
        } catch (e) {
            console.error("_loadArchivedKanbanItems failed", e);
            this.state.archivedKanbanItems = {};
        }
    }

    onLoadTemplateClick() {
        this.dialog.add(BrowseTemplatesDialog, {
            onTemplateApplied: async (templateId) => {
                try {
                    await this.orm.call(
                        "info.hub.article",
                        "apply_template_to_article",
                        [this.state.activeArticleId, templateId]
                    );

                    await this._loadData();
                    const currentId = this.state.activeArticleId;
                    this.state.activeArticleId = null;
                    await this.selectArticle(currentId);
                } catch {
                    this.notification.add("Failed to apply template.", { type: "danger" });
                }
            }
        });
    }

    onBuildItemKanbanClick() {
        if (!this.state.activeArticleId) return;
        const resId = this.state.activeArticleId;
        this.dialog.add(
            InsertKanbanViewDialog,
            {
                onInsert: async (name) => {
                    this.orm.call("info.hub.article", "create_default_item_stages", [resId])
                        .catch((err) => {
                            console.warn("Failed to pre-create default item stages:", err);
                        });

                    const embeddedProps = JSON.stringify({ viewProps: { resId, displayName: name } });
                    const block = renderToElement("info_hub.EmbeddedKanbanBlueprint", { embeddedProps });

                    const editor = this.editor;
                    if (editor && editor.editable) {
                        if (editor.shared?.dom?.insert) {
                            editor.editable.focus();
                            const doc = editor.editable.ownerDocument;
                            const win = doc.defaultView || window;
                            const sel = win.getSelection();
                            const range = doc.createRange();
                            range.selectNodeContents(editor.editable);
                            range.collapse(false);
                            sel.removeAllRanges();
                            sel.addRange(range);
                            editor.shared.dom.insert(block);
                        } else {
                            const doc = editor.editable.ownerDocument;
                            const trailingPara = doc.createElement("p");
                            trailingPara.innerHTML = "<br>";
                            editor.editable.appendChild(block);
                            editor.editable.appendChild(trailingPara);
                        }
                        if (editor.shared?.history?.addStep) {
                            editor.shared.history.addStep();
                        }
                        editor.config.onChange?.();
                    } else {
                        const bodyBlock = `<div data-embedded="kanban" data-embedded-props='${embeddedProps}' contenteditable="false" data-oe-protected="true"></div><p><br></p>`;
                        try {
                            await this.orm.write("info.hub.article", [resId], { body: bodyBlock });
                            await this._loadData();
                            const currentId = this.state.activeArticleId;
                            this.state.activeArticleId = null;
                            await this.selectArticle(currentId);
                        } catch {
                            this.notification.add("Failed to insert Kanban block.", { type: "danger" });
                        }
                    }
                    this.state.showEditorHelper = false;
                    window.dispatchEvent(new Event("info-set-full-width"));
                },
            }
        );
    }

    onBuildItemListClick() {
        if (!this.state.activeArticleId) return;
        const resId = this.state.activeArticleId;
        this.dialog.add(
            InsertListViewDialog,
            {
                onInsert: async (name) => {
                    const embeddedProps = JSON.stringify({ itemName: name });
                    const block = document.createElement("div");
                    block.dataset.embedded = "info_list";
                    block.dataset.embeddedProps = embeddedProps;
                    block.classList.add("o_info_list_host");

                    const editor = this.editor;
                    if (editor && editor.editable) {
                        if (editor.shared?.dom?.insert) {
                            editor.editable.focus();
                            const doc = editor.editable.ownerDocument;
                            const win = doc.defaultView || window;
                            const sel = win.getSelection();
                            const range = doc.createRange();
                            range.selectNodeContents(editor.editable);
                            range.collapse(false);
                            sel.removeAllRanges();
                            sel.addRange(range);
                            editor.shared.dom.insert(block);
                        } else {
                            const doc = editor.editable.ownerDocument;
                            const trailingPara = doc.createElement("p");
                            trailingPara.innerHTML = "<br>";
                            editor.editable.appendChild(block);
                            editor.editable.appendChild(trailingPara);
                        }
                        if (editor.shared?.history?.addStep) {
                            editor.shared.history.addStep();
                        }
                        editor.config.onChange?.();
                    } else {
                        const bodyBlock = `<div data-embedded="info_list" data-embedded-props='${embeddedProps}' class="o_info_list_host"></div><p><br></p>`;
                        try {
                            await this.orm.write("info.hub.article", [resId], { body: bodyBlock });
                            await this._loadData();
                            const currentId = this.state.activeArticleId;
                            this.state.activeArticleId = null;
                            await this.selectArticle(currentId);
                        } catch {
                            this.notification.add("Failed to insert List block.", { type: "danger" });
                        }
                    }

                    try {
                        await this.orm.write("info.hub.article", [resId], { is_full_width: true });
                        if (this.state.activeArticle) {
                            this.state.activeArticle.is_full_width = true;
                        }
                        window.dispatchEvent(new CustomEvent("info-set-full-width"));
                    } catch (err) {
                        console.warn("Failed to set article full width on list creation:", err);
                    }

                    this.state.showEditorHelper = false;
                },
            }
        );
    }

    onBuildItemCalendarClick() {
        if (!this.state.activeArticleId) return;
        const resId = this.state.activeArticleId;
        this.dialog.add(
            InsertCalendarViewDialog,
            {
                isAdvancedMode: false,
                onInsert: async (config) => {
                    const embeddedProps = JSON.stringify({
                        itemName: config.itemName,
                        scale: config.scale,
                        showWeekends: config.showWeekends,
                    });
                    const block = document.createElement("div");
                    block.dataset.embedded = "info_calendar";
                    block.dataset.embeddedProps = embeddedProps;
                    block.classList.add("o_info_calendar_host");

                    const editor = this.editor;
                    if (editor && editor.editable) {
                        if (editor.shared?.dom?.insert) {
                            editor.editable.focus();
                            const doc = editor.editable.ownerDocument;
                            const win = doc.defaultView || window;
                            const sel = win.getSelection();
                            const range = doc.createRange();
                            range.selectNodeContents(editor.editable);
                            range.collapse(false);
                            sel.removeAllRanges();
                            sel.addRange(range);
                            editor.shared.dom.insert(block);
                        } else {
                            const doc = editor.editable.ownerDocument;
                            const trailingPara = doc.createElement("p");
                            trailingPara.innerHTML = "<br>";
                            editor.editable.appendChild(block);
                            editor.editable.appendChild(trailingPara);
                        }
                        if (editor.shared?.history?.addStep) {
                            editor.shared.history.addStep();
                        }
                        editor.config.onChange?.();
                    } else {
                        const bodyBlock = `<div data-embedded="info_calendar" data-embedded-props='${embeddedProps}' class="o_info_calendar_host"></div><p><br></p>`;
                        try {
                            await this.orm.write("info.hub.article", [resId], { body: bodyBlock });
                            await this._loadData();
                            const currentId = this.state.activeArticleId;
                            this.state.activeArticleId = null;
                            await this.selectArticle(currentId);
                        } catch {
                            this.notification.add("Failed to insert Calendar block.", { type: "danger" });
                        }
                    }

                    try {
                        await this.orm.write("info.hub.article", [resId], { is_full_width: true });
                        if (this.state.activeArticle) {
                            this.state.activeArticle.is_full_width = true;
                        }
                        window.dispatchEvent(new CustomEvent("info-set-full-width"));
                    } catch (err) {
                        console.warn("Failed to set article full width on calendar creation:", err);
                    }

                    this.state.showEditorHelper = false;
                },
            }
        );
    }

    getKanbanItemsForApp() {
        return this.state.articles.filter((a) => {
            const pid = Array.isArray(a.parent_id) ? a.parent_id[0] : a.parent_id;
            return pid === this.state.activeArticleId;
        });
    }

    getKanbanViewProps() {
        if (!this.state.activeArticleId) return {};
        return {
            resModel: "info.hub.article",
            type: "kanban",
            views: [[this.state.kanbanViewId || false, "kanban"]],
            domain: [
                ["parent_id", "=", this.state.activeArticleId],
                ["is_article_item", "=", true],
            ],
            context: {
                default_parent_id: this.state.activeArticleId,
                default_is_article_item: true,
                default_category: this.state.activeArticle.category,
                active_test: false,
                active_id: this.state.activeArticleId,
            },
            groupBy: ["stage_id"],
            display: {},
            noContentHelp: markup(`<p class="o_view_nocontent_smiling_face">
                Create an Article Item
            </p>
            <p class="text-muted">
                Article items are articles that exist inside their parents but are not displayed in the menu. They can be used to handle lists (Buildings, Tasks, ...).
            </p>`),
            selectRecord: (resId) => this.selectArticle(resId),
        };
    }

    async onAddKanbanStage() {
        const name = prompt("Enter column name:");
        if (!name || !name.trim()) return;
        try {
            await this.orm.create("info.hub.article.stage", [{
                name: name.trim(),
                parent_id: this.state.activeArticleId,
                sequence: (this.state.kanbanStages.length + 1) * 10
            }]);
            await this._loadKanbanStages(this.state.activeArticleId);
        } catch {
            this.notification.add("Failed to add column.", { type: "danger" });
        }
    }

    async onRenameKanbanStage(stageId) {
        const stage = this.state.kanbanStages.find(s => s.id === stageId);
        if (!stage) return;
        const name = prompt("Enter new column name:", stage.name);
        if (!name || !name.trim()) return;
        try {
            await this.orm.write("info.hub.article.stage", [stageId], {
                name: name.trim()
            });
            await this._loadKanbanStages(this.state.activeArticleId);
        } catch {
            this.notification.add("Failed to rename column.", { type: "danger" });
        }
    }

    async onDeleteKanbanStage(stageId) {
        if (!confirm("Are you sure you want to delete this column and unlink all cards?")) return;
        try {
            await this.orm.unlink("info.hub.article.stage", [stageId]);
            await this._loadKanbanStages(this.state.activeArticleId);
            await this._loadData();
        } catch {
            this.notification.add("Failed to delete column.", { type: "danger" });
        }
    }

    async onAddKanbanItem(stageId) {
        const name = prompt("Enter card title:");
        if (!name || !name.trim()) return;
        try {
            const res = await this.orm.create("info.hub.article", [{
                name: name.trim(),
                parent_id: this.state.activeArticleId,
                category: this.state.activeArticle.category,
                stage_id: stageId,
                is_article_item: true,
                body: "",
            }]);
            const newId = Array.isArray(res) ? res[0] : res;
            await this._loadData();
            await this.selectArticle(newId);
        } catch {
            this.notification.add("Failed to create card.", { type: "danger" });
        }
    }

    onKanbanDragStart(itemId, ev) {
        this._dragItemId = itemId;
        ev.dataTransfer.setData("text/plain", itemId.toString());
        ev.dataTransfer.effectAllowed = "move";
    }

    onKanbanDragOver(ev) {
        ev.preventDefault();
    }

    async onKanbanDrop(targetStageId, ev) {
        ev.preventDefault();
        const itemId = this._dragItemId || Number(ev.dataTransfer.getData("text/plain"));
        if (!itemId) return;

        const item = this.state.articles.find(a => a.id === itemId);
        if (!item) return;

        try {
            await this.orm.write("info.hub.article", [itemId], {
                stage_id: targetStageId,
            });
            item.stage_id = [targetStageId, ""];
            this.state.articles = [...this.state.articles];
        } catch {
            this.notification.add("Failed to move card.", { type: "danger" });
        } finally {
            this._dragItemId = null;
        }
    }
}

/**
 * Extended list controller for embedded article-item list views.
 * Adds Information-specific record opening, creation via dialog, and full-screen navigation.
 */
export class InformationEmbeddedListController extends ListController {
    static template = "info_hub.InformationEmbeddedListView";
    static components = {
        ...ListController.components,
        Dropdown,
        DropdownItem,
    };
    static props = {
        ...ListController.props,
        listName: { type: String, optional: true },
        viewId: { type: [Number, Boolean], optional: true },
        onRename: { type: Function, optional: true },
        displayName: { type: String, optional: true },
        itemName: { type: String, optional: true },
        viewProps: { optional: true },
        host: { optional: true },
        "*": true,
    };

    setup() {
        super.setup();
        this.dialog = useService("dialog");
        this.action = useService("action");
        this.env.config.noBreadcrumbs = true;
        const title = this.props.listName || "Items";
        if (this.env.config.setDisplayName) {
            this.env.config.setDisplayName(title);
        }
    }

    async openRecord(record) {
        const dirty = await record.isDirty();
        if (dirty) {
            await record.save();
        }
        router.pushState({
            article_id: record.resId,
        });
        window.dispatchEvent(
            new CustomEvent("select-article", {
                detail: {
                    articleId: record.resId,
                },
            })
        );
    }

    async createRecord() {
        const parentId = this.props.context.default_parent_id || (router.current.article_id ? Number(router.current.article_id) : null);
        try {
            const res = await this.orm.create("info.hub.article", [{
                name: "Untitled",
                parent_id: parentId,
                is_article_item: true,
                body: "",
            }]);
            const newId = Array.isArray(res) ? res[0] : res;
            router.pushState({
                article_id: newId,
            });
            window.dispatchEvent(
                new CustomEvent("select-article", {
                    detail: {
                        articleId: newId,
                    },
                })
            );
        } catch (e) {
            console.error("Failed to create child article:", e);
        }
    }

    onExportAll() {
        this.exportRecords();
    }

    onOpenFullScreen() {
        const parentId = this.props.context.default_parent_id || (router.current.article_id ? Number(router.current.article_id) : null);
        this.action.doAction({
            name: this.props.listName || "Items",
            type: "ir.actions.act_window",
            res_model: "info.hub.article",
            views: [
                [this.props.viewId || false, "list"],
                [false, "form"],
            ],
            domain: [
                ["parent_id", "=", parentId],
                ["is_article_item", "=", true],
            ],
            context: {
                default_parent_id: parentId,
                default_is_article_item: true,
                default_name: "Untitled",
            },
        });
    }

    onEditListName() {
        this.dialog.add(InsertListViewDialog, {
            itemName: this.props.listName,
            onInsert: (newName) => {
                if (this.props.onRename) {
                    this.props.onRename(newName);
                }
                if (this.env.config.setDisplayName) {
                    this.env.config.setDisplayName(newName);
                }
            }
        });
    }

    async onRecordSaved(record) {
        await super.onRecordSaved(record);
        window.dispatchEvent(
            new CustomEvent("info-article-item-changed", {
                detail: { source: "embedded_list_" + this.props.context.active_id }
            })
        );
    }
}

export const infoEmbeddedListView = {
    ...listView,
    Controller: InformationEmbeddedListController,
    template: "info_hub.InformationEmbeddedListView",
};

registry.category("views").add("info_embedded_list", infoEmbeddedListView);

/**
 * OWL component that wraps an embedded list view of article items inside the article body.
 */
export class EmbeddedListViewComponent extends Component {
    static template = "info_hub.EmbeddedListViewComponent";
    static components = { View };
    static props = {
        host: { type: Object },
        itemName: { type: String, optional: true },
    };

    setup() {
        this.orm = useService("orm");
        const parentId = this.parentArticleId;
        this.state = useState({
            viewId: false,
            searchViewId: false,
            loading: true,
            itemName: this.props.itemName || "Todos",
            reloadKey: 0,
        });

        this.onItemChanged = (ev) => {
            if (ev.detail && ev.detail.source === "embedded_list_" + parentId) {
                return;
            }
            this.state.reloadKey++;
        };

        onMounted(() => {
            window.addEventListener("info-article-item-changed", this.onItemChanged);
        });

        onWillUnmount(() => {
            window.removeEventListener("info-article-item-changed", this.onItemChanged);
        });

        useSubEnv({
            config: {
                ...getDefaultConfig(),
                disableSearchBarAutofocus: true,
            },
            isEmbeddedView: true,
        });

        onWillStart(async () => {
            try {
                const records = await this.orm.searchRead(
                    "ir.model.data",
                    [
                        ["module", "=", "info_hub"],
                        ["name", "in", [
                            "info_article_view_tree_embedded",
                            "view_info_article_search",
                        ]],
                    ],
                    ["name", "res_id"]
                );
                for (const rec of records) {
                    if (rec.name === "info_article_view_tree_embedded") {
                        this.state.viewId = rec.res_id;
                    } else if (rec.name === "view_info_article_search") {
                        this.state.searchViewId = rec.res_id;
                    }
                }
            } catch (e) {
                console.error("Failed to fetch embedded list view IDs:", e);
            } finally {
                this.state.loading = false;
            }
        });
    }

    get parentArticleId() {
        return router.current.article_id ? Number(router.current.article_id) : null;
    }

    get viewProps() {
        const parentId = this.parentArticleId;
        return {
            type: "list",
            jsClass: "info_embedded_list",
            resModel: "info.hub.article",
            viewId: this.state.viewId || false,
            searchViewId: this.state.searchViewId || false,
            listName: this.state.itemName,
            loadActionMenus: true,
            onRename: (newName) => {
                this.state.itemName = newName;
                if (this.props.host) {
                    this.props.host.dataset.embeddedProps = JSON.stringify({ itemName: newName });
                    const editorEl = this.props.host.closest(".odoo-editor-editable");
                    if (editorEl) {
                        editorEl.dispatchEvent(new Event("input", { bubbles: true }));
                    }
                }
            },
            domain: [
                ["parent_id", "=", parentId],
                ["is_article_item", "=", true],
            ],
            context: {
                default_parent_id: parentId,
                default_is_article_item: true,
                default_name: "Untitled",
                search_default_articles: 0,
                search_default_my_articles: 0,
            },
            display: {
                controlPanel: {
                    "search-defaults": {},
                },
            },
        };
    }
}

/**
 * OWL Plugin that registers the "Insert List" powerbox command for embedding item list views.
 */
export class InformationListPlugin extends Plugin {
    static id = "infoList";
    static dependencies = ["dom", "selection", "embeddedComponents", "history", "dialog"];

    resources = {
        user_commands: [
            {
                id: "insertInformationList",
                title: _t("Item List"),
                description: _t("Insert a List view of article items"),
                icon: "fa-list-ul",
                run: this.openInsertDialog.bind(this),
                isAvailable: isHtmlContentSupported,
            }
        ],
        powerbox_items: [
            {
                categoryId: "structure",
                commandId: "insertInformationList",
            }
        ],
    };

    openInsertDialog() {
        let cursor = this.dependencies.selection.preserveSelection();
        this.services.dialog.add(
            InsertListViewDialog,
            {
                onInsert: (itemName) => {
                    cursor = null;
                    this.insertList(itemName);
                }
            },
            { onClose: () => cursor?.restore() }
        );
    }

    insertList(itemName) {
        const host = this.document.createElement("div");
        host.dataset.embedded = "info_list";
        host.dataset.embeddedProps = JSON.stringify({ itemName });
        host.classList.add("o_info_list_host");

        this.dependencies.dom.insert(host);
        this.dependencies.history.addStep();

        window.dispatchEvent(new CustomEvent("info-set-full-width"));
    }
}

/**
 * Extended calendar controller for embedded article-item calendar views.
 * Adds Information-specific record editing, creation dialog, and full-screen navigation.
 */
export class InformationEmbeddedCalendarController extends CalendarController {
    static template = "info_hub.InformationEmbeddedCalendarView";
    static components = {
        ...CalendarController.components,
        Dropdown,
        DropdownItem,
    };
    static props = {
        ...CalendarController.props,
        calendarName: { type: String, optional: true },
        scale: { type: String, optional: true },
        onRename: { type: Function, optional: true },
        displayName: { type: String, optional: true },
        itemName: { type: String, optional: true },
        viewProps: { optional: true },
        host: { optional: true },
        "*": true,
    };

    setup() {
        super.setup();
        this.orm = useService("orm");
        this.action = useService("action");
        this.dialog = useService("dialog");
        this.env.config.noBreadcrumbs = true;
    }

    async editRecord(record) {
        const resId = record.id;
        if (resId) {
            router.pushState({
                article_id: resId,
            });
            window.dispatchEvent(
                new CustomEvent("select-article", {
                    detail: {
                        articleId: resId,
                    },
                })
            );
        }
    }

    async createRecord(record) {
        const startUTC = record.start.toUTC().toFormat("yyyy-MM-dd HH:mm:ss");
        const endUTC = record.end ? record.end.toUTC().toFormat("yyyy-MM-dd HH:mm:ss") : startUTC;
        const parentId = this.props.context.default_parent_id || (router.current.article_id ? Number(router.current.article_id) : null);

        try {
            const res = await this.orm.create("info.hub.article", [{
                name: "Untitled",
                parent_id: parentId,
                is_article_item: true,
                item_date_start: startUTC,
                item_date_end: endUTC,
                body: "",
            }]);
            const newId = Array.isArray(res) ? res[0] : res;
            router.pushState({
                article_id: newId,
            });
            window.dispatchEvent(
                new CustomEvent("select-article", {
                    detail: {
                        articleId: newId,
                        reload: true,
                    },
                })
            );
        } catch (e) {
            console.error("Failed to create child article via calendar cell click:", e);
        }
    }

    async onCreateClick() {
        const parentId = this.props.context.default_parent_id || (router.current.article_id ? Number(router.current.article_id) : null);
        try {
            const res = await this.orm.create("info.hub.article", [{
                name: "Untitled",
                parent_id: parentId,
                is_article_item: true,
                body: "",
            }]);
            const newId = Array.isArray(res) ? res[0] : res;
            router.pushState({
                article_id: newId,
            });
            window.dispatchEvent(
                new CustomEvent("select-article", {
                    detail: {
                        articleId: newId,
                        reload: true,
                    },
                })
            );
        } catch (e) {
            console.error("Failed to create child article via calendar New button:", e);
        }
    }

    onOpenFullScreen() {
        const parentId = this.props.context.default_parent_id || (router.current.article_id ? Number(router.current.article_id) : null);
        this.action.doAction({
            name: this.props.calendarName || "Meetings",
            type: "ir.actions.act_window",
            res_model: "info.hub.article",
            views: [
                [this.props.viewId || false, "calendar"],
                [false, "form"],
            ],
            domain: [
                ["parent_id", "=", parentId],
                ["is_article_item", "=", true],
            ],
            context: {
                default_parent_id: parentId,
                default_is_article_item: true,
                default_name: "Untitled",
            },
        });
    }

    onEditCalendarName() {
        this.dialog.add(InsertCalendarViewDialog, {
            itemName: this.props.calendarName,
            scale: this.env.config.viewProps?.mode || "week",
            showWeekends: this.state.isWeekendVisible,
            isAdvancedMode: true,
            onInsert: (config) => {
                const newName = config.itemName;
                if (this.props.onRename) {
                    this.props.onRename(newName, config.scale, config.showWeekends);
                }
            }
        });
    }
}

export const infoEmbeddedCalendarView = {
    ...calendarView,
    Controller: InformationEmbeddedCalendarController,
    template: "info_hub.InformationEmbeddedCalendarView",
};

registry.category("views").add("info_embedded_calendar", infoEmbeddedCalendarView);

/**
 * OWL component that wraps an embedded calendar view of article items inside the article body.
 */
export class EmbeddedCalendarViewComponent extends Component {
    static template = "info_hub.EmbeddedCalendarViewComponent";
    static components = { View };
    static props = {
        host: { type: Object },
        itemName: { type: String, optional: true },
        scale: { type: String, optional: true },
        showWeekends: { type: Boolean, optional: true },
    };

    setup() {
        this.orm = useService("orm");
        this.state = useState({
            viewId: false,
            searchViewId: false,
            loading: true,
            itemName: this.props.itemName || "Meetings",
            scale: this.props.scale || "week",
            showWeekends: this.props.showWeekends !== undefined ? this.props.showWeekends : true,
        });

        onWillStart(async () => {
            try {
                const records = await this.orm.searchRead(
                    "ir.model.data",
                    [
                        ["module", "=", "info_hub"],
                        ["name", "in", [
                            "info_article_view_calendar_embedded",
                            "view_info_article_search",
                        ]],
                    ],
                    ["name", "res_id"]
                );
                for (const rec of records) {
                    if (rec.name === "info_article_view_calendar_embedded") {
                        this.state.viewId = rec.res_id;
                    } else if (rec.name === "view_info_article_search") {
                        this.state.searchViewId = rec.res_id;
                    }
                }
            } catch (e) {
                console.error("Failed to fetch embedded calendar view IDs:", e);
            } finally {
                this.state.loading = false;
            }
        });

        onWillUpdateProps((nextProps) => {
            if (nextProps.itemName !== undefined) {
                this.state.itemName = nextProps.itemName;
            }
            if (nextProps.scale !== undefined) {
                this.state.scale = nextProps.scale;
            }
            if (nextProps.showWeekends !== undefined) {
                this.state.showWeekends = nextProps.showWeekends;
            }
        });
    }

    get parentArticleId() {
        return router.current.article_id ? Number(router.current.article_id) : null;
    }

    get viewProps() {
        const parentId = this.parentArticleId;
        const scale = this.state.scale || "week";
        const showWeekends = this.state.showWeekends !== undefined ? this.state.showWeekends : true;
        const viewId = this.state.viewId;
        if (viewId) {
            window.localStorage.setItem(`scaleOf-viewId-${viewId}`, scale);
        }
        window.localStorage.setItem("calendar.isWeekendVisible", JSON.stringify(showWeekends));

        return {
            type: "calendar",
            jsClass: "info_embedded_calendar",
            resModel: "info.hub.article",
            viewId: viewId || false,
            searchViewId: this.state.searchViewId || false,
            calendarName: this.state.itemName,
            scale: scale,
            mode: scale,
            loadActionMenus: false,
            onRename: (newName, newScale, newShowWeekends) => {
                this.state.itemName = newName;
                this.state.scale = newScale || "week";
                this.state.showWeekends = newShowWeekends !== undefined ? newShowWeekends : this.state.showWeekends;
                if (this.props.host) {
                    this.props.host.dataset.embeddedProps = JSON.stringify({
                        itemName: newName,
                        scale: this.state.scale,
                        showWeekends: this.state.showWeekends,
                    });
                    const editorEl = this.props.host.closest(".odoo-editor-editable");
                    if (editorEl) {
                        editorEl.dispatchEvent(new Event("input", { bubbles: true }));
                    }
                }
            },
            domain: [
                ["parent_id", "=", parentId],
                ["is_article_item", "=", true],
            ],
            context: {
                default_parent_id: parentId,
                default_is_article_item: true,
                default_name: this.state.itemName || "Untitled",
                default_mode: scale,
            },
        };
    }
}

/**
 * OWL Plugin that registers the "Insert Calendar" powerbox command for embedding item calendar views.
 */
export class InformationCalendarPlugin extends Plugin {
    static id = "infoCalendar";
    static dependencies = ["dom", "selection", "embeddedComponents", "history", "dialog"];

    resources = {
        user_commands: [
            {
                id: "insertInformationCalendar",
                title: _t("Item Calendar"),
                description: _t("Insert a Calendar view of article items"),
                icon: "fa-calendar",
                run: this.openInsertDialog.bind(this),
                isAvailable: isHtmlContentSupported,
            }
        ],
        powerbox_items: [
            {
                categoryId: "structure",
                commandId: "insertInformationCalendar",
            }
        ],
    };

    async openInsertDialog() {
        let cursor = this.dependencies.selection.preserveSelection();
        const resId = this.config.getRecordInfo?.()?.resId;
        let isAdvancedMode = false;
        if (this.document.querySelector(".o_info_calendar_host")) {
            isAdvancedMode = true;
        } else if (resId) {
            try {
                const count = await this.services.orm.searchCount("info.hub.article", [
                    ["parent_id", "=", resId],
                    ["is_article_item", "=", true],
                ]);
                if (count > 0) {
                    isAdvancedMode = true;
                }
            } catch (err) {
                console.error("Failed to check existing calendar articles:", err);
            }
        }
        this.services.dialog.add(
            InsertCalendarViewDialog,
            {
                isAdvancedMode: isAdvancedMode,
                onInsert: (config) => {
                    cursor = null;
                    this.insertCalendar(config);
                }
            },
            { onClose: () => cursor?.restore() }
        );
    }

    insertCalendar(config) {
        const host = this.document.createElement("div");
        host.dataset.embedded = "info_calendar";
        host.dataset.embeddedProps = JSON.stringify({
            itemName: config.itemName,
            scale: config.scale,
            showWeekends: config.showWeekends,
        });
        host.classList.add("o_info_calendar_host");

        this.dependencies.dom.insert(host);
        this.dependencies.history.addStep();

        window.dispatchEvent(new CustomEvent("info-set-full-width"));
    }
}

registry.category("actions").add("info_hub.InfoApp", InfoApp);
