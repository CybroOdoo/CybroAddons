import { registry } from "@web/core/registry";

registry.category("web_tour.tours").add("odoo_website_helpdesk_form_tour", {
    url: "/helpdesk_ticket",
    steps: () => [
        {
            content: "Enter the name",
            trigger: "#ticket_form input[name=customer_name]",
            run: "edit Tour Visitor",
        },
        {
            content: "Enter the email",
            trigger: "#ticket_form input[name=email_from]",
            run: "edit tour@example.com",
        },
        {
            content: "Enter the subject",
            trigger: "#ticket_form input[name=subject]",
            run: "edit Tour printer issue",
        },
        {
            content: "Describe the issue",
            trigger: "#ticket_form textarea[name=description]",
            run: "edit The printer shows an error",
        },
        {
            content: "Submit the ticket",
            trigger: "#ticket_form .s_website_form_send",
            run: "click",
            expectUnloadPage: true,
        },
        {
            content: "The ticket is created",
            trigger: ".o_helpdesk_ticket_created:contains(has been created successfully)",
        },
    ],
});

registry.category("web_tour.tours").add("odoo_website_helpdesk_portal_tour", {
    url: "/my/tickets",
    steps: () => [
        {
            content: "Both tickets are listed",
            trigger: ".search_ticket:contains(Printer jam):contains(Screen flicker)",
        },
        {
            content: "Search a ticket",
            trigger: "#search_box",
            run: "edit Printer",
        },
        {
            content: "Run the search",
            trigger: "#search_ticket",
            run: "click",
        },
        {
            content: "Only the matching ticket is listed",
            trigger: ".search_ticket:contains(Printer jam):not(:contains(Screen flicker))",
        },
        {
            content: "Group the tickets by stage",
            trigger: "#group_select",
            run: "select 1",
        },
        {
            content: "The tickets are grouped",
            trigger: ".search_ticket th:contains(Inbox)",
        },
        {
            content: "Open a ticket",
            trigger: ".search_ticket a:contains(TKT)",
            run: "click",
            expectUnloadPage: true,
        },
        {
            content: "The ticket is shown",
            trigger: "#helpdesk_content:contains(The printer does not start)",
        },
    ],
});
