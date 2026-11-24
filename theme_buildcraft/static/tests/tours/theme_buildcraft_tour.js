/** @odoo-module **/

import { registry } from "@web/core/registry";

registry.category("web_tour.tours").add("theme_buildcraft_tour", {
    test: true,
    url: "/blog",
    steps: () => [
        {
            content: "Visitors can sign in from the header",
            trigger: ".nav-user a[href*='/web/login']",
            isCheck: true,
        },
        {
            content: "Type an email address in the newsletter form",
            trigger: ".bc-newsletter-form input[name='email_from']",
            run: "text tour.reader@example.com",
        },
        {
            content: "Subscribe",
            trigger: ".bc-newsletter-form .s_website_form_send",
        },
        {
            content: "The subscription is confirmed",
            trigger: ".bc-newsletter-form .s_website_form_end_message:not(.d-none)",
            isCheck: true,
        },
        {
            content: "Open the Projects page from the header",
            trigger: ".nav-desktop-links a[href='/projects']",
        },
        {
            content: "Show the luxury projects",
            trigger: ".project-filter-tab[data-filter='luxury']",
        },
        {
            content: "No luxury project: the empty message shows",
            trigger: "#no-filtered-projects-msg:visible",
            isCheck: true,
        },
        {
            content: "Show the residential projects",
            trigger: ".project-filter-tab[data-filter='residential']",
        },
        {
            content: "The residential project shows, and the empty message is hidden",
            trigger: ".project-grid-card:contains('Palm Villa'):visible",
            extra_trigger: "body:not(:has(#no-filtered-projects-msg:visible))",
            isCheck: true,
        },
    ],
});
