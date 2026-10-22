import { registry } from "@web/core/registry";

registry.category("web_tour.tours").add("restrict_web_debug_tour", {
    steps: () => [
        {
            content: "Wait for the webclient navbar to load",
            trigger: ".o_main_navbar",
        },
        {
            content: "Check that the debug manager is not present in the DOM for restricted user",
            trigger: "body:not(:has(.o_debug_manager))",
        },
    ],
});

registry.category("web_tour.tours").add("unrestricted_web_debug_tour", {
    steps: () => [
        {
            content: "Wait for the debug manager button to be present for unrestricted user in debug mode",
            trigger: ".o_debug_manager button",
        },
    ],
});
