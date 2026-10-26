/** @odoo-module **/
/**
 * Compliance dashboard: loads, switches period and opens the manifest
 * drill-down. Run by wm_compliance/tests/test_ui_compliance_dashboard.py.
 */
import { registry } from "@web/core/registry";

registry.category("web_tour.tours").add("wm_compliance_dashboard_tour", {
    steps: () => [
        {
            content: "The dashboard is rendered",
            trigger: ".wm_compliance_dashboard_root .wm_cd_title:contains(Compliance Control Center)",
        },
        {
            content: "Switch to the monthly period",
            trigger: ".wm_compliance_dashboard_root .time_pill:contains(Month)",
            run: "click",
        },
        {
            content: "Open the in-transit manifests drill-down",
            trigger: ".wm_compliance_dashboard_root .kpi_manifests .sub_item:contains(transit)",
            run: "click",
        },
        {
            content: "The manifest list opens",
            trigger: ".o_list_view, .o_view_nocontent",
        },
    ],
});
