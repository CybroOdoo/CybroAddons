/**
 * Operations dashboard: loads, switches period and opens the revenue
 * drill-down built from the server-provided order revenue domain.
 * Run by wm_base/tests/test_ui_dashboard.py.
 */
import { registry } from "@web/core/registry";

registry.category("web_tour.tours").add("wm_dashboard_tour", {
    steps: () => [
        {
            content: "The dashboard is rendered",
            trigger: ".wm_dashboard_root .wm_db_title:contains(Operations Dashboard)",
        },
        {
            content: "Switch to the monthly period",
            trigger: ".wm_dashboard_root .time_pill:contains(Month)",
            run: "click",
        },
        {
            content: "Open the pending orders drill-down",
            trigger: ".wm_dashboard_root .kpi_orders .kpi_main_val_wrap",
            run: "click",
        },
        {
            content: "The drill-down list opens",
            trigger: ".o_list_view, .o_view_nocontent",
        },
    ],
});

registry.category("web_tour.tours").add("wm_dashboard_revenue_tour", {
    steps: () => [
        {
            content: "The dashboard is rendered",
            trigger: ".wm_dashboard_root .kpi_revenue",
        },
        {
            content: "Open the collection order revenue drill-down",
            trigger: ".wm_dashboard_root .kpi_revenue [title='View Collection Orders']",
            run: "click",
        },
        {
            content: "The drill-down lists collection orders",
            trigger: ".o_breadcrumb:contains(Revenue)",
        },
        {
            content: "The list (or its empty state) is shown",
            trigger: ".o_list_view, .o_view_nocontent",
        },
    ],
});

registry.category("web_tour.tours").add("wm_dashboard_basic_tour", {
    steps: () => [
        {
            content: "The dashboard is rendered",
            trigger: ".wm_dashboard_root .wm_db_title:contains(Operations Dashboard)",
        },
        {
            content: "Switch to the monthly period",
            trigger: ".wm_dashboard_root .time_pill:contains(Month)",
            run: "click",
        },
        {
            content: "The monthly figures are shown",
            trigger: ".wm_dashboard_root .kpi_revenue .kpi_main_val_wrap",
        },
        {
            content: "Cards of uninstalled modules are hidden",
            trigger: ".wm_dashboard_root .wm_db_top_kpi_row:not(:has(.kpi_orders))",
        },
    ],
});
