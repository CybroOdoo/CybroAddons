import { registry } from "@web/core/registry";

registry.category("web_tour.tours").add("advanced_chatter_view_tour", {
    steps: () => [
        {
            content: "Check collapsed action buttons exist and click Send Message",
            trigger: ".o_adv_chatter_actions #send_message",
            run: "click",
        },
        {
            content: "Check chatter expanded with Send Message filter",
            trigger: ".o-adv-chatter-expanded.o-adv-filter-message",
        },
        {
            content: "Close chatter via cross button",
            trigger: ".o_adv_chatter_close_btn",
            run: "click",
        },
        {
            content: "Check chatter collapsed and click Log Note",
            trigger: ".o_adv_chatter_actions #log_note",
            run: "click",
        },
        {
            content: "Check chatter expanded with Log Note filter",
            trigger: ".o-adv-chatter-expanded.o-adv-filter-note",
        },
        {
            content: "Close chatter via cross button",
            trigger: ".o_adv_chatter_close_btn",
            run: "click",
        },
        {
            content: "Check chatter collapsed and click Activities",
            trigger: ".o_adv_chatter_actions #active",
            run: "click",
        },
        {
            content: "Check chatter expanded with Activities filter",
            trigger: ".o-adv-chatter-expanded.o-adv-filter-activity",
        },
        {
            content: "Close chatter back to collapsed state",
            trigger: ".o_adv_chatter_close_btn",
            run: "click",
        },
        {
            content: "Verify chatter is collapsed",
            trigger: ".o_adv_chatter_actions #send_message",
        },
    ],
});
