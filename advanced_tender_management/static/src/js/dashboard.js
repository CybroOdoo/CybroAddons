import { Component, onWillStart, useProps } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useChart } from "@web/core/utils/chart_hook";
import { useService } from "@web/core/utils/hooks";
import { standardActionServiceProps } from "@web/webclient/actions/action_plugin";

const NO_GRID = { x: { grid: { display: false } }, y: { grid: { display: false } } };

/**
 * Tender dashboard: counters and charts of tenders and bids.
 */
export class TenderDashboard extends Component {
    static template = "advanced_tender_management.TenderDashboard";
    props = useProps(standardActionServiceProps);
    tenderTypeChart = useChart(() => this.getTenderTypeConfig());
    categoryChart = useChart(() => this.getCategoryConfig());
    timelineChart = useChart(() => this.getTimelineConfig());

    setup() {
        this.orm = useService("orm");
        onWillStart(async () => {
            this.data = await this.orm.call("tender.management", "get_tender_details", []);
        });
    }

    getTenderTypeConfig() {
        const { tender_types, tender_type_count } = this.data.tender_type_data;
        return {
            type: "pie",
            data: {
                labels: tender_types,
                datasets: [{ label: "Tender Type", data: tender_type_count }],
            },
        };
    }

    getCategoryConfig() {
        const { category_types, category_type_count } = this.data.tender_category_data;
        return {
            type: "bar",
            data: {
                labels: category_types,
                datasets: [{ label: "Tenders", data: category_type_count }],
            },
            options: { scales: NO_GRID },
        };
    }

    getTimelineConfig() {
        const { tenders, tender_timeline_data } = this.data.tender_timeline_data;
        return {
            type: "line",
            data: {
                labels: tenders,
                datasets: [{ label: "Tender Duration", data: tender_timeline_data }],
            },
            options: {
                scales: {
                    x: { grid: { display: false } },
                    y: { grid: { display: false }, ticks: { callback: (value) => `${value} days` } },
                },
            },
        };
    }
}

registry.category("actions").add("tender_dashboard_tag", TenderDashboard);
