import { registry } from "@web/core/registry";

registry.category("web_tour.tours").add("whatsapp_chat_layout_tour", {
    steps: () => [
        {
            trigger: ".o-mail-Discuss",
        },
        {
            trigger: ".wa-sidebar-header",
        },
        {
            trigger: ".wa-tab-btn[data-icon='mail']",
        },
        {
            trigger: ".wa-tab-btn[data-icon='chat_bubble']",
        },
        {
            trigger: ".wa-tab-btn[data-icon='tag']",
        },
        {
            trigger: ".wa-tab-btn[data-icon='videocam']",
        },
    ],
});

