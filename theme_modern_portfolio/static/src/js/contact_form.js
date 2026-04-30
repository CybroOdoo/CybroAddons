import { registry } from "@web/core/registry";
import { Interaction } from "@web/public/interaction";

export class ContactForm extends Interaction {
    static selector = ".s_contact_form";
    dynamicContent = {
        '.source-field .dropdown-option': {
            "t-on-click": (ev) => this.clicked('source_input', ev),
        },
        '.timeline-field .dropdown-option': {
            "t-on-click": (ev) => this.clicked('timeline_input', ev),
        },
        '.discuss-field .dropdown-option': {
            "t-on-click": (ev) => this.clicked('discuss_input', ev),
        },
    }
    clicked(id, ev){
        this.el.querySelector(`#${id}`).value = ev.target.innerText;
    }
}
registry.category("public.interactions").add("theme_modern_portfolio.contact_form", ContactForm);