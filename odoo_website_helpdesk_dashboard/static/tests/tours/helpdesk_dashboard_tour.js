import { registry } from "@web/core/registry";
import { stepUtils } from "@web_tour/tour_utils";

function checkChart(selector, expected) {
    const chart = Chart.getChart(document.querySelector(`${selector} canvas`));
    const values = chart && chart.data.datasets[0].data.join(",");
    if (values !== expected) {
        throw new Error(`The chart ${selector} shows ${values} instead of ${expected}`);
    }
}

registry.category("web_tour.tours").add("helpdesk_dashboard_tour", {
    steps: () => [
        ...stepUtils.goToAppSteps("odoo_website_helpdesk.menu_helpdesk", "Open the HelpDesk app"),
        {
            content: "The app opens on the dashboard with the new tickets",
            trigger: ".o_helpdesk_card_new .o_helpdesk_card_count:contains(2)",
        },
        {
            content: "The in progress and done tickets and the teams are counted",
            trigger: ".o_helpdesk_card_in_progress .o_helpdesk_card_count:contains(2)",
        },
        {
            trigger: ".o_helpdesk_card_done .o_helpdesk_card_count:contains(1)",
        },
        {
            trigger: ".o_helpdesk_card_teams .o_helpdesk_card_count:contains(2)",
        },
        {
            content: "The reviewed tickets are counted",
            trigger: ".o_helpdesk_review_count:contains(1)",
        },
        {
            content: "The priority bars show the share of each priority",
            trigger: ".o_helpdesk_priority_1 .o_helpdesk_priority_percent:contains(40%)",
        },
        {
            content: "The status chart is drawn",
            trigger: ".o_helpdesk_status_chart canvas",
            run: () => checkChart(".o_helpdesk_status_chart", "2,2,1"),
        },
        {
            content: "The team chart is drawn",
            trigger: ".o_helpdesk_team_chart canvas",
            run: () => checkChart(".o_helpdesk_team_chart", "3,1"),
        },
        {
            content: "The latest tickets are listed",
            trigger: ".o_helpdesk_tickets tbody tr:contains(Ticket 4)",
        },
        {
            content: "Open the tickets in progress",
            trigger: ".o_helpdesk_card_in_progress",
            run: "click",
        },
        {
            content: "Only the tickets in progress are listed",
            trigger: ".o_list_renderer:has(.o_data_row:contains(Ticket 2)):has(.o_data_row:contains(Ticket 3))",
            run() {
                const rows = document.querySelectorAll(".o_list_renderer .o_data_row");
                if (rows.length !== 2) {
                    throw new Error(`${rows.length} tickets listed instead of 2`);
                }
            },
        },
        {
            content: "Go back to the dashboard",
            trigger: ".o_breadcrumb .breadcrumb-item a",
            run: "click",
        },
        {
            content: "Open a ticket from the list",
            trigger: ".o_helpdesk_tickets tbody tr:contains(Ticket 4)",
            run: "click",
        },
        {
            content: "The ticket form is opened",
            trigger: ".o_form_view .o_field_widget[name=subject]:contains(Ticket 4), .o_form_view .o_field_widget[name=subject] textarea:value(Ticket 4)",
        },
    ],
});
