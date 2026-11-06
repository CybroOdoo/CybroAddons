/** @odoo-module **/
/**
 * Petzen contact page: the "Quick Answers" FAQ accordion.
 * The form itself is Odoo's website form (#contactus_form, s_website_form widget).
 */
import publicWidget from "@web/legacy/js/public/public_widget";

publicWidget.registry.PetzenContactFaq = publicWidget.Widget.extend({
    selector: ".pz-page-contact",
    events: {
        "click .ct-faq-q": "_onFaqClick",
    },

    _onFaqClick(ev) {
        const item = ev.currentTarget.closest(".ct-faq-item");
        const wasOpen = item.classList.contains("open");
        this.el.querySelectorAll(".ct-faq-item").forEach((i) => i.classList.remove("open"));
        if (!wasOpen) {
            item.classList.add("open");
        }
    },
});
