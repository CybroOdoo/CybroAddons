/** @odoo-module **/

import {Plugin} from "@html_editor/plugin";
import {_t} from "@web/core/l10n/translation";
import {isHtmlContentSupported} from "@html_editor/core/selection_plugin";
import {ArticleSearchDialog} from "./article_search_dialog";
import {router, routerBus} from "@web/core/browser/router";
import {InsertKanbanViewDialog} from "./info_hub_templates_dialog";

/**
 * Editor plugin that provides article-link insertion functionality for the community Information module.
 * Registers a powerbox command for inserting internal article links into the editor body.
 */
export class ArticlePluginCommunity extends Plugin {
    static id = "articleCommunity";
    static dependencies = ["dom", "selection", "history", "dialog"];

    resources = {
        user_commands: [
            {
                id: "insertArticle",
                title: _t("Article"),
                description: _t("Insert an Article shortcut"),
                icon: "fa-newspaper-o",
                isAvailable: isHtmlContentSupported,
                run: () => {
                    this.insertArticle();
                },
            },
            {
                id: "insertInformationCard",
                title: _t("Item Cards"),
                description: _t("Insert a Card view of article items"),
                icon: "fa-address-card-o",
                isAvailable: isHtmlContentSupported,
                run: () => {
                    this.insertCard();
                },
            },
        ],
        powerbox_items: [
            {
                commandId: "insertArticle",
                categoryId: "navigation",
            },
            {
                commandId: "insertInformationCard",
                categoryId: "structure",
            },
        ],
        clean_for_save_handlers: this.cleanForSave.bind(this),
        normalize_handlers: this.normalize.bind(this),
    };

    setup() {

        this.addGlobalDomListener("click", this.onClick.bind(this));
    }

    insertArticle() {
        const cursors = this.dependencies.selection.preserveSelection();

        this.services.dialog.add(ArticleSearchDialog, {
            onArticleSelected: (article) => {
                cursors.restore();

                const link = this.document.createElement("span");
                link.textContent = "📄 " + article.name;
                link.classList.add("o_info_article_link");
                link.setAttribute("contenteditable", "false");
                link.dataset.res_id = article.id;

                this.dependencies.dom.insert(link);
                this.dependencies.history.addStep();
            }
        });
    }

    insertCard() {
        const resId = this.config.getRecordInfo?.()?.resId;
        if (!resId) return;

        const cursors = this.dependencies.selection.preserveSelection();

        this.services.dialog.add(InsertKanbanViewDialog, {
            onInsert: async (name) => {
                cursors.restore();

                const orm = this.services.orm;
                if (orm) {
                    orm.call("info.hub.article", "create_default_item_stages", [resId])
                        .catch((err) => {
                            console.warn("Failed to pre-create default item stages:", err);
                        });
                }

                const embeddedProps = JSON.stringify({ viewProps: { resId, displayName: name } });
                const host = this.document.createElement("div");
                host.dataset.embedded = "info_card";
                host.dataset.embeddedProps = embeddedProps;
                host.className = "o_info_card_host d-flex flex-column my-3";
                host.setAttribute("contenteditable", "false");
                host.setAttribute("data-oe-protected", "true");

                this.dependencies.dom.insert(host);
                this.dependencies.history.addStep();
                this.config.onChange?.();
                window.dispatchEvent(new CustomEvent("info-set-full-width"));
            }
        });
    }

    scanForArticleLinks(element) {
        if (!element || !element.querySelectorAll) {
            return [];
        }

        const articleLinks = [...element.querySelectorAll(".o_info_article_link")];
        if (element.matches && element.matches(".o_info_article_link")) {
            articleLinks.unshift(element);
        }
        return articleLinks;
    }

    normalize(element) {
        for (const articleLink of this.scanForArticleLinks(element)) {
            articleLink.setAttribute("contenteditable", "false");
        }
    }

    cleanForSave({root}) {
        for (const articleLink of this.scanForArticleLinks(root)) {
            articleLink.removeAttribute("contenteditable");
        }
    }

    onClick(ev) {
        if (!this.editable.contains(ev.target)) return;

        const link = ev.target.closest(".o_info_article_link");

        if (!link) return;

        ev.preventDefault();
        const articleId = link.dataset.res_id;
        if (!articleId) return;

        if (this.config.onClickArticle) {
            this.config.onClickArticle(parseInt(articleId));
        } else {
            router.pushState({article_id: parseInt(articleId)});
            routerBus.trigger("ROUTE_CHANGE");
        }
    }
}
