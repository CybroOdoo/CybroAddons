/** @odoo-module **/

import { registry } from "@web/core/registry";

registry.category("web_tour.tours").add("theme_converza_case_filter", {
    test: true,
    url: "/case-studies",
    steps: () => [
        {
            content: "Filter the case studies on e-commerce",
            trigger: ".case-filter-btn[href='#ecommerce']",
            run: "click",
        },
        {
            content: "The e-commerce case is shown",
            trigger: ".case-card#ecommerce:visible",
        },
        {
            content: "The other cases are hidden",
            trigger: ".case-card#healthcare:not(:visible)",
            run: () => {},
        },
        {
            content: "Show all industries again",
            trigger: ".case-filter-btn:first",
            run: "click",
        },
        {
            content: "All the cases are back",
            trigger: ".case-card#healthcare:visible",
        },
    ],
});

registry.category("web_tour.tours").add("theme_converza_pricing_toggle", {
    test: true,
    url: "/pricing",
    steps: () => [
        {
            content: "Switch to annual billing",
            trigger: ".billing-toggle-wrap .toggle-switch",
            run: "click",
        },
        {
            content: "The annual price is displayed",
            trigger: ".price-num:contains('1,199')",
            run: () => {},
        },
        {
            content: "Switch back to monthly billing",
            trigger: ".billing-toggle-wrap .toggle-switch",
            run: "click",
        },
        {
            content: "The monthly price is displayed",
            trigger: ".price-num:contains('1,499')",
            run: () => {},
        },
    ],
});

registry.category("web_tour.tours").add("theme_converza_counters", {
    test: true,
    url: "/result",
    steps: () => [
        {
            content: "Wait for the counter animation to end on the final value",
            trigger: ".roi-num[data-count='312']:contains('312%')",
            run: () => {},
        },
    ],
});
