/** @odoo-module **/
import { Plugin } from "@html_editor/plugin";
import { registry } from "@web/core/registry";
import { BaseOptionComponent } from "@html_builder/core/base_option_component";
import { BuilderAction } from "@html_builder/core/builder_action";

const SNIPPET_SELECTOR = ".s_special_products_options";
const DEFAULT_TEMPLATE = "special_product_snippet.first_dynamic_template";

function getSnippetElement(el) {
    return el && el.closest ? (el.closest(SNIPPET_SELECTOR) || el) : el;
}

export class SpecialProductOption extends BaseOptionComponent {
    static id = "special_product_option";
    static template = "special_product_snippet.SpecialProductOption";
}

/**
 * Both actions only write to the snippet's dataset. That is deliberate: the
 * mutation is recorded by the editor (so the view is flagged dirty and the
 * change is saved) and the builder restarts the interaction on normalization,
 * which re-renders the body. Triggering the re-render from here -- e.g. with a
 * setTimeout'd custom event -- would run outside the current operation and race
 * with the history save points, which is what silently reverted the change.
 */
export class SpecialProductTemplateAction extends BuilderAction {
    static id = "specialProductTemplate";

    getValue({ editingElement: el }) {
        const snippetEl = getSnippetElement(el);
        return snippetEl.dataset.templateKey || DEFAULT_TEMPLATE;
    }

    isApplied({ editingElement: el, value }) {
        const snippetEl = getSnippetElement(el);
        return (snippetEl.dataset.templateKey || DEFAULT_TEMPLATE) === value;
    }

    apply({ editingElement: el, value }) {
        getSnippetElement(el).dataset.templateKey = value;
    }
}

export class SpecialProductRecordAction extends BuilderAction {
    static id = "specialProductRecord";

    getValue({ editingElement: el }) {
        const snippetEl = getSnippetElement(el);
        const id = snippetEl.dataset.productId;
        if (id) {
            return JSON.stringify({ id: parseInt(id) });
        }
    }

    apply({ editingElement: el, value }) {
        const snippetEl = getSnippetElement(el);
        if (!value) {
            delete snippetEl.dataset.productId;
            return;
        }
        let id;
        if (typeof value === "string") {
            try {
                const parsed = JSON.parse(value);
                id = parsed ? parsed.id || parsed : undefined;
            } catch {
                id = parseInt(value);
            }
        } else if (typeof value === "object" && value !== null) {
            id = value.id;
        } else {
            id = parseInt(value);
        }
        if (id) {
            snippetEl.dataset.productId = id;
            if (!snippetEl.dataset.templateKey) {
                snippetEl.dataset.templateKey = DEFAULT_TEMPLATE;
            }
        } else {
            delete snippetEl.dataset.productId;
        }
    }

    clean({ editingElement: el }) {
        delete getSnippetElement(el).dataset.productId;
    }
}

export class SpecialProductPlugin extends Plugin {
    static id = "specialProductPlugin";
    resources = {
        builder_actions: {
            SpecialProductTemplateAction,
            SpecialProductRecordAction,
        },
        clean_for_save_processors: (root) => {
            // The interaction already empties the container in its destroy(),
            // which runs before the save. This is only a safety net for the
            // case where the interaction never started.
            const targets = [
                ...(root.matches && root.matches(SNIPPET_SELECTOR) ? [root] : []),
                ...root.querySelectorAll(SNIPPET_SELECTOR),
            ];
            for (const el of targets) {
                const container = el.querySelector(":scope > .container");
                if (container) {
                    container.replaceChildren();
                }
            }
            return root;
        },
    };
}

registry.category("website-options").add(SpecialProductOption.id, SpecialProductOption);
registry.category("website-plugins").add(SpecialProductPlugin.id, SpecialProductPlugin);

