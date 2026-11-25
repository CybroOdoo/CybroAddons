/**
 * Petzen contact page: the "Quick Answers" FAQ accordion.
 * The form itself is Odoo's website form (#contactus_form, s_website_form).
 */
import { registry } from "@web/core/registry";
import { Interaction } from "@web/public/interaction";

export class PetzenContactFaq extends Interaction {
    static selector = ".pz-page-contact";
    dynamicContent = {
        ".ct-faq-q": { "t-on-click": this.onFaqClick },
    };

    /**
     * Open the clicked question (only one open at a time), or close it.
     *
     * @param {MouseEvent} ev
     */
    onFaqClick(ev) {
        const item = ev.currentTarget.closest(".ct-faq-item");
        const wasOpen = item.classList.contains("open");
        this.el.querySelectorAll(".ct-faq-item").forEach((i) => i.classList.remove("open"));
        if (!wasOpen) {
            item.classList.add("open");
        }
    }
}

registry.category("public.interactions").add("theme_petzen.contact_faq", PetzenContactFaq);
