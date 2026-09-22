/** @odoo-module **/
import { Interaction } from "@web/public/interaction";
import { registry } from "@web/core/registry";
import { rpc } from "@web/core/network/rpc";

/**
 * Renders the snippet body from data-product-id / data-template-key, on every
 * page load, in both edit mode and the live site.
 *
 * The arch only ever carries the two data attributes; the body is rebuilt here
 * on every start. Two rules must be respected for that to survive a save:
 *
 * 1. Every DOM write must happen in a "protected" context, i.e. while the
 *    editor's mutation observer is off. Code running after `await waitFor()`
 *    is *not* protected anymore, hence `protectSyncAfterAsync`. Writing the
 *    rendered markup unprotected made the editor record it as a real edit; the
 *    next option change then took a history save point over that garbage and,
 *    on revert (any preview/commit cycle of a builder option), restored the
 *    previous product together with its stale markup.
 * 2. The body must be removed again in `destroy()`, like core's dynamic
 *    snippet does. Interactions are stopped before the save, so the cloned
 *    arch never contains generated markup.
 */
export class SpecialProductInteraction extends Interaction {
    static selector = ".s_special_products_options";

    setup() {
        this.hasRendered = false;
    }

    async willStart() {
        await this.renderProduct();
    }

    destroy() {
        // Never let generated markup reach the saved arch (or the next start).
        if (this.hasRendered) {
            this.getContainer().replaceChildren();
            this.hasRendered = false;
        }
    }

    getContainer() {
        return this.el.querySelector(":scope > .container") || this.el;
    }

    async renderProduct() {
        const productId = parseInt(this.el.dataset.productId || 0);
        const templateKey = this.el.dataset.templateKey;

        if (!productId || !templateKey) {
            return;
        }

        let response;
        try {
            response = await this.waitFor(
                rpc("/website/snippet/special/render", {
                    id: productId,
                    template: templateKey,
                })
            );
        } catch {
            // Leave the placeholder in place rather than blanking the section.
            return;
        }

        if (!response?.html) {
            return;
        }

        // /!\ Protected: we are past an await, the editor observer is back on.
        this.protectSyncAfterAsync(() => {
            this.getContainer().innerHTML = response.html;
            this.hasRendered = true;
        })();
    }
}

registry
    .category("public.interactions")
    .add("special_product_snippet.special_product", SpecialProductInteraction);

// Also run inside the website builder iframe, so the editor shows the same thing
// the visitor will see. The builder restarts the interaction by itself whenever
// the snippet's dataset changes (see Interaction.getConfigurationSnapshot), so
// no manual refresh signal is needed -- and none must be sent, as it would run
// outside of the current editor operation.
registry
    .category("public.interactions.edit")
    .add("special_product_snippet.special_product", {
        Interaction: SpecialProductInteraction,
    });
