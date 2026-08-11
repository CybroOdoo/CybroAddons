import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { Component, onWillStart, proxy, useRef, onMounted, onWillUnmount } from "@odoo/owl";
import { loadJS } from "@web/core/assets";

export class BrandDashboard extends Component {
    static template = "product_brand_saas.BrandDashboard";

    setup() {
        this.orm = useService("orm");
        this.actionService = useService("action");
        this.barChartRef = useRef("brandBarChart");
        this.pieChartRef = useRef("brandPieChart");
        this.barChartInstance = null;
        this.pieChartInstance = null;

        let userName = "Manager";
        if (window.odoo && window.odoo.session_info) {
            userName = window.odoo.session_info.partner_name || window.odoo.session_info.username || "Manager";
        }

        this.state = proxy({
            userName: userName.split(" ")[0],
            brands: [],
            stages: [],
            categories: [],
            searchQuery: "",
            filterStage: "all",
            stats: {
                totalBrands: 0,
                totalProducts: 0,
                totalCategories: 0,
                totalTags: 0,
            }
        });

        onWillStart(async () => {
            await this.loadStages();
            await this.loadData();
            await this.loadChartJs();
        });

        onMounted(() => {
            this.renderCharts();
            this.refreshInterval = setInterval(() => {
                this.loadData();
            }, 10000);
        });

        onWillUnmount(() => {
            if (this.refreshInterval) {
                clearInterval(this.refreshInterval);
            }
        });
    }

    async loadChartJs() {
        if (window.Chart) return;
        return loadJS("/web/static/lib/Chart/Chart.js");
    }

    async loadStages() {
        try {
            this.state.stages = await this.orm.searchRead("x_brands_stage", [], ["id", "x_name"]);
        } catch (e) {
            console.error("Failed to load stages", e);
        }
    }

    async loadData() {
        try {
            // Fetch brands
            const brands = await this.orm.searchRead(
                "x_brands",
                [],
                [
                    "x_name",
                    "x_studio_brand_code",
                    "x_studio_category",
                    "x_studio_stage_id",
                    "x_x_studio_brands_product_template_count"
                ],
                { order: "id desc" }
            );

            this.state.brands = brands;

            // Fetch categories count
            const totalCategories = await this.orm.searchCount("x_brand_category", []);
            // Fetch tags count
            const totalTags = await this.orm.searchCount("x_brand_tags", []);

            // Calculate Stats
            let totalProducts = 0;

            for (const b of brands) {
                totalProducts += b.x_x_studio_brands_product_template_count || 0;
            }

            this.state.stats = {
                totalBrands: brands.length,
                totalProducts: totalProducts,
                totalCategories: totalCategories,
                totalTags: totalTags,
            };

            if (this.barChartRef.el && this.pieChartRef.el) {
                this.renderCharts();
            }
        } catch (e) {
            console.error("Failed to load brand data", e);
        }
    }

    getFilteredBrands() {
        return this.state.brands.filter(b => {
            if (this.state.filterStage !== "all") {
                const stageId = b.x_studio_stage_id ? b.x_studio_stage_id[0] : false;
                if (stageId !== this.state.filterStage) {
                    return false;
                }
            }
            if (this.state.searchQuery) {
                const query = this.state.searchQuery.toLowerCase();
                const name = (b.x_name || "").toLowerCase();
                const code = (b.x_studio_brand_code || "").toLowerCase();
                if (!name.includes(query) && !code.includes(query)) {
                    return false;
                }
            }
            return true;
        });
    }

    getStageBadgeStyle(stageName) {
        if (!stageName) return "font-size: 0.75rem; font-weight: 600; background-color: #F1F5F9 !important; color: #475569 !important;";
        const name = stageName.toLowerCase();
        if (name.includes("new") || name.includes("draft")) {
            return "font-size: 0.75rem; font-weight: 600; background-color: #E0F2FE !important; color: #0369A1 !important;";
        } else if (name.includes("progress") || name.includes("active")) {
            return "font-size: 0.75rem; font-weight: 600; background-color: #DCFCE7 !important; color: #166534 !important;";
        } else if (name.includes("cancel") || name.includes("blocked")) {
            return "font-size: 0.75rem; font-weight: 600; background-color: #FEE2E2 !important; color: #991B1B !important;";
        }
        return "font-size: 0.75rem; font-weight: 600; background-color: #FEF9C3 !important; color: #854D0E !important;";
    }

    onSearchInput(ev) {
        this.state.searchQuery = ev.target.value;
    }

    changeFilterStage(stageId) {
        this.state.filterStage = stageId;
    }

    openBrand(brandId) {
        this.actionService.doAction({
            type: "ir.actions.act_window",
            res_model: "x_brands",
            res_id: brandId,
            views: [[false, "form"]],
            target: "current",
        });
    }

    createBrand() {
        this.actionService.doAction({
            type: "ir.actions.act_window",
            res_model: "x_brands",
            views: [[false, "form"]],
            target: "new",
        });
    }

    formatCurrency(amount) {
        return new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD', maximumFractionDigits: 0 }).format(amount);
    }

    renderCharts() {
        if (!window.Chart) {
            setTimeout(() => this.renderCharts(), 100);
            return;
        }

        // 1. Products by Brand Bar Chart
        if (this.barChartInstance) {
            this.barChartInstance.destroy();
        }
        const barCtx = this.barChartRef.el;
        if (barCtx) {
            const sortedBrands = [...this.state.brands]
                .sort((a, b) => (b.x_x_studio_brands_product_template_count || 0) - (a.x_x_studio_brands_product_template_count || 0))
                .slice(0, 6);

            let labels = sortedBrands.map(b => b.x_name || "Unnamed");
            let data = sortedBrands.map(b => b.x_x_studio_brands_product_template_count || 0);

            if (data.reduce((a, b) => a + b, 0) === 0) {
                labels = ["Brand A", "Brand B", "Brand C", "Brand D"];
                data = [12, 19, 8, 15];
            }

            this.barChartInstance = new window.Chart(barCtx, {
                type: 'bar',
                data: {
                    labels: labels,
                    datasets: [{
                        label: 'Product Count',
                        data: data,
                        backgroundColor: '#6366f1',
                        borderRadius: 6,
                        barPercentage: 0.4,
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: { display: false },
                    },
                    scales: {
                        y: {
                            beginAtZero: true,
                            ticks: { precision: 0 }
                        }
                    }
                }
            });
        }

        // 2. Brand Category Wise Distribution Pie Chart
        if (this.pieChartInstance) {
            this.pieChartInstance.destroy();
        }
        const pieCtx = this.pieChartRef.el;
        if (pieCtx) {
            const categoryCounts = {};
            for (const b of this.state.brands) {
                const catName = b.x_studio_category ? b.x_studio_category[1] : "Uncategorized";
                categoryCounts[catName] = (categoryCounts[catName] || 0) + 1;
            }

            // Sort categories by brand count descending
            const sortedCats = Object.entries(categoryCounts)
                .sort((a, b) => b[1] - a[1])
                .slice(0, 6);

            let labels = sortedCats.map(c => c[0]);
            let data = sortedCats.map(c => c[1]);

            if (data.length === 0) {
                labels = ["Uncategorized"];
                data = [0];
            }

            this.pieChartInstance = new window.Chart(pieCtx, {
                type: 'doughnut',
                data: {
                    labels: labels,
                    datasets: [{
                        data: data,
                        backgroundColor: ['#f43f5e', '#06b6d4', '#10b981', '#6366f1', '#fbbf24', '#a855f7'],
                        borderWidth: 2,
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: { position: 'right' }
                    }
                }
            });
        }
    }
}

registry.category("actions").add("brand_dashboard_client_action", BrandDashboard);
