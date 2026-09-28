/** @odoo-module **/

import { Component, onWillStart, useState, useSubEnv, markup, onMounted, onWillUnmount } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";
import { View } from "@web/views/view";
import { getEmbeddedProps } from "@html_editor/others/embedded_component_utils";
import { getDefaultConfig } from "@web/views/view";
import { CallbackRecorder } from "@web/search/action_hook";
import { KanbanController } from "@web/views/kanban/kanban_controller";
import { kanbanView } from "@web/views/kanban/kanban_view";
import { router } from "@web/core/browser/router";
import { registry } from "@web/core/registry";
import { InsertKanbanViewDialog } from "./info_hub_templates_dialog";

/**
 * OWL component that renders an embedded kanban board of article items inside the article body.
 * Loads stages from the parent article and forwards drag-and-drop stage changes to the ORM.
 */
export class EmbeddedKanbanComponent extends Component {
    static template = "info_hub.EmbeddedKanban";
    static components = { View };
    static props = {
        host: { type: Object },
        viewProps: { type: Object },
    };
    static actionCache = null;

    setup() {
        this.actionService = useService("action");
        const resId = this.props.viewProps.resId;
        this.state = useState({ isLoaded: false, error: false, reloadKey: 0 });

        this.onItemChanged = (ev) => {
            if (ev.detail && ev.detail.source === "embedded_kanban_" + resId) {
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
                const resId = this.props.viewProps.resId;
                if (!EmbeddedKanbanComponent.actionCache) {
                    EmbeddedKanbanComponent.actionCache = await this.actionService.loadAction(
                        "info_hub.action_info_article_item_kanban",
                        {
                            active_id: resId,
                            default_parent_id: resId,
                            default_is_article_item: true,
                        }
                    );
                }

                this.action = JSON.parse(JSON.stringify(EmbeddedKanbanComponent.actionCache));

                const displayName = this.props.viewProps.displayName || "Items";
                this.action.name = `Kanban of ${displayName}`;
                this.action.display_name = this.action.name;

                if (this.env.config) {
                    this.env.config.views = this.action.views;
                    if (typeof this.env.config.setDisplayName === "function") {
                        this.env.config.setDisplayName(this.action.name);
                    }
                }

                this.__getGlobalState__ = new CallbackRecorder();
                this.state.isLoaded = true;
            } catch (e) {
                console.error("EmbeddedKanbanComponent: failed to load action", e);
                this.state.error = true;
            }
        });
    }

    get displayName() {
        const name = this.props.viewProps.displayName;
        return name ? `Kanban of ${name}` : "Kanban Board";
    }

    get embeddedViewProps() {
        const resId = this.props.viewProps.resId;
        return {
            viewId: this.action.views?.find(([, t]) => t === "kanban")?.[0] || false,
            searchViewId: this.action.searchViewId?.[0] || false,
            type: "kanban",
            jsClass: "info_embedded_kanban",
            resModel: "info.hub.article",
            domain: [["is_article_item", "=", true], ["parent_id", "=", resId]],
            context: {
                active_id: resId,
                default_parent_id: resId,
                default_is_article_item: true,
                search_default_articles: 0,
                search_default_my_articles: 0,
            },
            groupBy: ["stage_id"],
            loadActionMenus: true,
            loadIrFilters: true,
            limit: 20,
            noContentHelp: this.action.help ? markup(this.action.help) : false,
            __getGlobalState__: this.__getGlobalState__,
            displayName: this.displayName,
        };
    }

    openFullView() {
        if (!this.action) return;
        const resId = this.props.viewProps.resId;
        this.actionService.doAction({
            ...this.action,
            context: {
                ...this.action.context,
                active_id: resId,
                default_parent_id: resId,
            },
        });
    }
}

export const kanbanEmbedding = {
    name: "kanban",
    Component: EmbeddedKanbanComponent,
    getProps: (host) => ({ host, ...getEmbeddedProps(host) }),
};

/**
 * Extended kanban controller for Information article items.
 * Overrides record opening to navigate within the Information app and hooks into record saves.
 */
export class InformationEmbeddedKanbanController extends KanbanController {
    static props = {
        ...KanbanController.props,
        displayName: { type: String, optional: true },
        itemName: { type: String, optional: true },
        viewProps: { optional: true },
        host: { optional: true },
        "*": true,
    };

    async openRecord(record, { newWindow } = {}) {
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

    onRecordSaved(record) {
        super.onRecordSaved(record);
        window.dispatchEvent(
            new CustomEvent("info-article-item-changed", {
                detail: { source: "embedded_kanban_" + this.props.context.active_id }
            })
        );
    }

    onOpenFullScreen() {
        const parentId = this.props.context.active_id;
        this.env.services.action.doAction({
            name: this.props.displayName || "Article Items",
            type: "ir.actions.act_window",
            res_model: "info.hub.article",
            views: [
                [false, "kanban"],
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
        this.env.services.dialog.add(InsertKanbanViewDialog, {
            itemName: this.props.displayName,
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
}

export const infoEmbeddedKanbanView = {
    ...kanbanView,
    Controller: InformationEmbeddedKanbanController,
};

registry.category("views").add("info_embedded_kanban", infoEmbeddedKanbanView);
