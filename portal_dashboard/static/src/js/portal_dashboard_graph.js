import { Interaction } from "@web/public/interaction";
import { registry } from "@web/core/registry";
import { rpc } from "@web/core/network/rpc";
import { loadBundle } from "@web/core/assets";

export class PortalDashboardGraph extends Interaction {
    static selector = ".portal_dashboard";

    async willStart() {
        await loadBundle("web.chartjs_lib");
        this.charts = [];
    }

    async start() {
        await this.renderCharts();
    }

    destroy() {
        if (this.charts) {
            for (const chart of this.charts) {
                if (chart && typeof chart.destroy === "function") {
                    chart.destroy();
                }
            }
            this.charts = [];
        }
        super.destroy();
    }

    _createOrUpdateChart(canvas, config) {
        if (!canvas) {
            return null;
        }
        if (window.Chart.getChart) {
            const existing = window.Chart.getChart(canvas);
            if (existing && typeof existing.destroy === "function") {
                existing.destroy();
            }
        }
        const chart = new window.Chart(canvas, config);
        this.charts.push(chart);
        return chart;
    }

    async renderCharts() {
        const result = await rpc("/web/dataset/call_kw", {
            model: "portal.dashboard.data",
            method: "datafetch",
            args: [],
            kwargs: {},
        });

        if (!window.Chart || !result) {
            return;
        }

        const salesCanvas = this.el.querySelector("#sales_pie");
        if (salesCanvas && result.target) {
            this._createOrUpdateChart(salesCanvas, {
                type: "pie",
                data: {
                    labels: ["Sales Orders", "Quotations"],
                    datasets: [
                        {
                            label: "Sales",
                            data: result.target,
                            backgroundColor: ["#2f4f4f", "#0f7f7f"],
                        },
                    ],
                },
                options: {
                    responsive: true,
                    plugins: {
                        legend: { position: "top" },
                        title: { display: true, text: "Sales Analysis" },
                    },
                },
            });
        }

        const purchaseCanvas = this.el.querySelector("#purchase_pie");
        if (purchaseCanvas && result.target_po) {
            this._createOrUpdateChart(purchaseCanvas, {
                type: "pie",
                data: {
                    labels: ["Purchase Orders", "RFQs"],
                    datasets: [
                        {
                            label: "Purchases",
                            data: result.target_po,
                            backgroundColor: ["#6b6363", "#879393"],
                        },
                    ],
                },
                options: {
                    responsive: true,
                    plugins: {
                        legend: { position: "top" },
                        title: { display: true, text: "Purchase Analysis" },
                    },
                },
            });
        }

        const accountCanvas = this.el.querySelector("#account_pie");
        if (accountCanvas && result.target_accounting) {
            this._createOrUpdateChart(accountCanvas, {
                type: "pie",
                data: {
                    labels: ["Invoices", "Bills"],
                    datasets: [
                        {
                            label: "Accounting",
                            data: result.target_accounting,
                            backgroundColor: ["#cf6363", "#ebb393"],
                        },
                    ],
                },
                options: {
                    responsive: true,
                    plugins: {
                        legend: { position: "top" },
                        title: { display: true, text: "Accounting Analysis" },
                    },
                },
            });
        }
    }
}

registry
    .category("public.interactions")
    .add("portal_dashboard.graph", PortalDashboardGraph);
