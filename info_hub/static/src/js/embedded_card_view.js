/** @odoo-module **/

import { Component, onWillStart, useState, useSubEnv, markup, onMounted, onWillUnmount } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";
import { View } from "@web/views/view";
import { getEmbeddedProps } from "@html_editor/others/embedded_component_utils";
import { getDefaultConfig } from "@web/views/view";
import { registry } from "@web/core/registry";
import { InformationEmbeddedKanbanController } from "./embedded_kanban";
import { kanbanView } from "@web/views/kanban/kanban_view";
import { router } from "@web/core/browser/router";
import { Dropdown } from "@web/core/dropdown/dropdown";
import { DropdownItem } from "@web/core/dropdown/dropdown_item";
import { InsertKanbanViewDialog } from "./info_hub_templates_dialog";

export class InformationEmbeddedCardsController extends InformationEmbeddedKanbanController {
    static template = "info_hub.InfoEmbeddedCardsView";
    static components = {
        ...InformationEmbeddedKanbanController.components,
        Dropdown,
        DropdownItem,
    };
    static props = {
        ...InformationEmbeddedKanbanController.props,
        displayName: { type: String, optional: true },
        onRename: { type: Function, optional: true },
    };

    get activeActions() {
        return this.props.activeActions || { create: true };
    }

    async createRecord() {
        const parentId = this.props.context.active_id;
        const orm = this.env.services.orm;
        
        const childIds = await orm.create("info.hub.article", [{
            parent_id: parentId,
            is_article_item: true,
            name: "Untitled",
        }]);
        const childId = childIds[0];
        
        router.pushState({
            article_id: childId,
        });
        window.dispatchEvent(
            new CustomEvent("select-article", {
                detail: {
                    articleId: childId,
                },
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

    onEditCardsName() {
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

export const infoEmbeddedCardsView = {
    ...kanbanView,
    Controller: InformationEmbeddedCardsController,
};

registry.category("views").add("info_embedded_cards", infoEmbeddedCardsView);

/**
 * EmbeddedCardViewComponent
 *
 * Renders a flat live Odoo Kanban card view of article items inside the article editor.
 */
export class EmbeddedCardViewComponent extends Component {
    static template = "info_hub.EmbeddedCardView";
    static components = { View };
    static props = {
        host: { type: Object },
        viewProps: { type: Object },
    };

    setup() {
        this.actionService = useService("action");
        this.orm = useService("orm");
        const resId = this.props.viewProps.resId;
        this.state = useState({
            isLoaded: false,
            error: false,
            reloadKey: 0,
            cardViewId: false,
            displayName: this.props.viewProps.displayName || "Article Items",
        });

        this.onItemChanged = (ev) => {
            if (ev.detail && ev.detail.source === "embedded_card_" + resId) {
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

        const originalOrm = this.env.services.orm;
        let customOrm = originalOrm;
        if (originalOrm) {
            customOrm = Object.create(originalOrm);
            customOrm.call = async (model, method, args, kwargs) => {
                const res = await originalOrm.call(model, method, args, kwargs);
                if (
                    ["info.hub.article", "info.hub.article.stage"].includes(model) &&
                    ["create", "write", "unlink", "web_save_multi", "name_create", "web_save"].includes(method)
                ) {
                    window.dispatchEvent(new CustomEvent("info-article-item-changed", {
                        detail: { source: "embedded_card_" + resId }
                    }));
                }
                return res;
            };
            Object.defineProperty(customOrm, "silent", {
                get() {
                    const silentOrm = Object.create(originalOrm.silent);
                    silentOrm.call = customOrm.call;
                    return silentOrm;
                }
            });
        }

        useSubEnv({
            config: {
                ...getDefaultConfig(),
                disableSearchBarAutofocus: true,
            },
            services: {
                ...this.env.services,
                orm: customOrm,
            },
            isEmbeddedView: true,
        });

        onWillStart(async () => {
            try {
                // Fetch the database ID of the embedded cards view
                const viewId = await this.orm.call("info.hub.article", "get_embedded_card_view_id", []);
                this.state.cardViewId = viewId;
                
                if (this.env.config) {
                    this.env.config.views = [[viewId || false, "kanban"]];
                    if (typeof this.env.config.setDisplayName === "function") {
                        this.env.config.setDisplayName(this.state.displayName);
                    }
                }
                
                this.state.isLoaded = true;
            } catch (e) {
                console.error("EmbeddedCardViewComponent: failed to load card view ID", e);
                this.state.error = true;
            }
        });
    }

    get articleId() {
        return this.props.viewProps.resId;
    }

    onRename(newName) {
        this.state.displayName = newName;
        if (this.props.host) {
            this.props.host.dataset.embeddedProps = JSON.stringify({
                viewProps: {
                    resId: this.props.viewProps.resId,
                    displayName: newName,
                }
            });
            const editorEl = this.props.host.closest(".odoo-editor-editable");
            if (editorEl) {
                editorEl.dispatchEvent(new Event("input", { bubbles: true }));
            }
        }
    }

    get embeddedViewProps() {
        return {
            views: [[this.state.cardViewId || false, "kanban"]],
            type: "kanban",
            jsClass: "info_embedded_cards", // Reuses click-to-open logic but customizes creation routing
            resModel: "info.hub.article",
            domain: [["parent_id", "=", this.articleId], ["is_article_item", "=", true]],
            context: {
                active_id: this.articleId,
                default_parent_id: this.articleId,
                default_is_article_item: true,
                force_embedded_cards: true,
                display_name: this.state.displayName,
            },
            loadActionMenus: false,
            loadIrFilters: false,
            limit: 20,
            displayName: this.state.displayName,
            display_name: this.state.displayName,
            onRename: this.onRename.bind(this),
            useSampleModel: false,
            action: {
                id: 0,
                name: this.state.displayName,
                res_model: "info.hub.article",
                type: "ir.actions.act_window",
                context: {
                    active_id: this.articleId,
                    default_parent_id: this.articleId,
                    default_is_article_item: true,
                    force_embedded_cards: true,
                    display_name: this.state.displayName,
                },
                flags: {
                    create: true,
                    edit: true,
                    delete: true,
                },
            },
        };
    }
}

export const infoCardEmbedding = {
    name: "info_card",
    Component: EmbeddedCardViewComponent,
    getProps: (host) => ({ host, ...getEmbeddedProps(host) }),
};
