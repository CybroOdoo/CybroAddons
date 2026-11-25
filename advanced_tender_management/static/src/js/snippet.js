import { rpc } from "@web/core/network/rpc";
import { registry } from "@web/core/registry";
import { Interaction } from "@web/public/interaction";

/**
 * Website snippet listing the tenders open for bidding.
 */
export class TenderManagementSnippet extends Interaction {
    static selector = ".dynamic_snippet_blog";

    async willStart() {
        this.tenders = await this.waitFor(rpc("/tender_management_snippet"));
    }

    start() {
        const carouselEl = this.el.querySelector("#carousel");
        const placeholderEl = this.el.querySelector(".o_tender_snippet_placeholder");
        if (placeholderEl) {
            placeholderEl.classList.add("d-none");
            this.registerCleanup(() => placeholderEl.classList.remove("d-none"));
        }
        if (carouselEl) {
            this.renderAt(
                "advanced_tender_management.tender_snippet_carousel",
                { tenders: this.tenders },
                carouselEl
            );
        }
    }
}

registry
    .category("public.interactions")
    .add("advanced_tender_management.tender_management_snippet", TenderManagementSnippet);
