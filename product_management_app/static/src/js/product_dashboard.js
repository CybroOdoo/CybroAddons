/** @odoo-module **/
import { registry } from "@web/core/registry";
import { Component, onWillStart, onMounted, proxy, signal } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";
import { loadBundle } from "@web/core/assets";
export class ProductDashboard extends Component{
    /**
     * Setup lifecycle hook.
     * Initializes services, references, state variables,
     * and registers lifecycle hooks for data fetching
     * and chart rendering.
     */
    setup(){
        super.setup(...arguments);
        this.orm = useService("orm");
        this.TopSaleChart = signal(null)
        this.TopPurchaseChart = signal(null)
        this.ProductChart = signal(null)
        this.ProductQtyChart = signal(null)
        this.YearSelection = signal(null)
        this.ProductSelection = signal(null)
        this.ProductLocation = signal(null)
        this.state = proxy({
                product_templates : [],
                variants_count : [],
                products_storable : [],
                product_consumable: [],
                product_service: [],
                product_pricelist : [],
                product_attribute:[],
                location_chart: [],
                move_chart: [],
            });
        onWillStart(async () => {
            await loadBundle("web.chartjs_lib");
            await this.fetch_data();
        });
        onMounted(async ()=> {
            await this.render_top_sold_product();
            await this.render_top_purchase_product();
            await this.render_year_chart ();
            await this.render_monthly_chart ();
            await this.onchange_prod_selection();
            await this.render_product_categ_analysis();
            await this.onchange_location_selection();
        });
    }
    async fetch_data() {
        var self = this
        var result = await this.orm.call('product.template', "get_data", [])
        this.state.product_templates = result['product_templates'] || 0
        this.state.variants_count = result['product_variants'] || 0
        this.state.products_storable = result['combo'] || 0
        this.state.product_consumable = result['goods'] || 0
        this.state.product_service = result['service'] || 0
        this.state.product_categ = result['category'] || 0
        this.state.product_pricelist = result['price_list'] || 0
        this.state.product_attribute = result['product_attribute'] || 0
    }
    async render_top_sold_product() {
        var self = this
        var ctx = this.TopSaleChart();
        if (!ctx) return;
        if (this.topSaleChartInstance) {
            this.topSaleChartInstance.destroy();
            this.topSaleChartInstance = null;
        }
        const arrays = await this.orm.call('product.template', "get_top_sale_data", [])
        const rawData = (arrays && arrays[0]) || [];
        const rawLabels = (arrays && arrays[1]) || [];
        const hasData = rawData.length > 0 && rawData.some(val => Number(val) > 0);

        var data = {
            labels: hasData ? rawLabels : [],
            datasets: [{
                label: "",
                data: hasData ? rawData : [],
                backgroundColor: [
                    "#1E90FF",
                    "#95B9C7",
                    "#66CDAA",
                    "#FF7F50",
                    "#F67280",
                    "#810541",
                    "#7D0552",
                    "#D58A94",
                    "#B041FF"
                ],
                borderColor: [
                    "#1E90FF",
                    "#95B9C7",
                    "#66CDAA",
                    "#FF7F50",
                    "#F67280",
                    "#810541",
                    "#7D0552",
                    "#D58A94",
                    "#B041FF"
                ],
                borderWidth: 1
            }]
        };
        var options = {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: hasData,
                    position: "right",
                    labels: {
                        boxWidth: 12,
                        padding: 10,
                        font: {
                            size: 12
                        }
                    }
                }
            }
        };
        const emptyStatePlugin = {
            id: 'emptyStateTopSales',
            afterDraw: (chart) => {
                if (!hasData) {
                    const { ctx, width, height } = chart;
                    ctx.save();
                    ctx.textAlign = 'center';
                    ctx.textBaseline = 'middle';
                    ctx.font = '500 14px system-ui, -apple-system, sans-serif';
                    ctx.fillStyle = '#94a3b8';
                    ctx.fillText('No sales data available', width / 2, height / 2);
                    ctx.restore();
                }
            }
        };
        this.topSaleChartInstance = new Chart(ctx, {
            type: "pie",
            data: data,
            options: options,
            plugins: [emptyStatePlugin]
        });
    }
    async render_top_purchase_product() {
        var self = this
        var ctx = this.TopPurchaseChart();
        if (!ctx) return;
        if (this.topPurchaseChartInstance) {
            this.topPurchaseChartInstance.destroy();
            this.topPurchaseChartInstance = null;
        }
        const arrays = await this.orm.call('product.template', "get_top_purchase_data", [])
        const rawData = (arrays && arrays[0]) || [];
        const rawLabels = (arrays && arrays[1]) || [];
        const hasData = rawData.length > 0 && rawData.some(val => Number(val) > 0);

        var data = {
            labels: hasData ? rawLabels : [],
            datasets: [{
                label: "",
                data: hasData ? rawData : [],
                backgroundColor: [
                    "#003f5c",
                    "#2f4b7c",
                    "#f95d6a",
                    "#665191",
                    "#d45087",
                    "#ff7c43",
                    "#ffa600",
                    "#a05195",
                    "#6d5c16"
                ],
                borderColor: [
                    "#003f5c",
                    "#2f4b7c",
                    "#f95d6a",
                    "#665191",
                    "#d45087",
                    "#ff7c43",
                    "#ffa600",
                    "#a05195",
                    "#6d5c16"
                ],
                borderWidth: 1
            }]
        };
        var options = {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: hasData,
                    position: "right",
                    labels: {
                        boxWidth: 12,
                        padding: 10,
                        font: {
                            size: 12
                        }
                    }
                }
            }
        };
        const emptyStatePlugin = {
            id: 'emptyStateTopPurchases',
            afterDraw: (chart) => {
                if (!hasData) {
                    const { ctx, width, height } = chart;
                    ctx.save();
                    ctx.textAlign = 'center';
                    ctx.textBaseline = 'middle';
                    ctx.font = '500 14px system-ui, -apple-system, sans-serif';
                    ctx.fillStyle = '#94a3b8';
                    ctx.fillText('No purchase data available', width / 2, height / 2);
                    ctx.restore();
                }
            }
        };
        this.topPurchaseChartInstance = new Chart(ctx, {
            type: "doughnut",
            data: data,
            options: options,
            plugins: [emptyStatePlugin]
        });
    }
    async render_year_chart() {
        var self = this
        const data = await this.orm.call('product.template', "get_years", [])
        const select = this.YearSelection();
        if (select) {
            select.innerHTML = '';
            (data || []).forEach(year => {
                const option = document.createElement("option");
                option.value = year;
                option.textContent = year;
                select.appendChild(option);
            });
        }
    }
    async render_monthly_chart() {
        var self = this
        const data = await this.orm.call('product.template', "get_products", [])
        const products = this.ProductSelection();
        if (products) {
            products.innerHTML = '';
            const entries = Object.entries((data && data.product_name) || {});
            if (entries.length === 0) {
                const option = document.createElement("option");
                option.value = "";
                option.textContent = "No products available";
                products.appendChild(option);
            } else {
                var k = 0;
                entries.forEach(([key, value]) => {
                    const option = document.createElement("option");
                    option.value = data.product_id[k];
                    option.textContent = typeof value === 'object' && value !== null ? (value.en_US || Object.values(value)[0] || '') : value;
                    if (k == 0) {
                        option.selected = true;
                    }
                    products.appendChild(option);
                    k++;
                });
            }
        }
    }
    async onchange_prod_selection() {
        if (this.moveChartInstance) {
            this.moveChartInstance.destroy();
            this.moveChartInstance = null;
        }
        var productElement = this.ProductSelection();
        var option = productElement ? productElement.value : null;
        var yearElement = this.YearSelection();
        var year = yearElement ? yearElement.value : null;
        var ctx = this.ProductChart();
        if (!ctx) return;

        let result = { dates: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'], count: [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0] };
        if (option && year) {
            result = await this.orm.call('product.template', "get_prod_details", [option, year]);
        }
        const hasData = result.count && result.count.some(val => Number(val) > 0);

        var data = {
            labels: result.dates,
            datasets: [{
                label: 'Units Moved',
                data: result.count,
                backgroundColor: 'rgba(59, 130, 246, 0.15)',
                borderColor: '#3b82f6',
                borderWidth: 2,
                pointBackgroundColor: '#3b82f6',
                pointRadius: hasData ? 4 : 0,
                tension: 0.35,
                fill: true
            }]
        };
        var options = {
            scales: {
                y: {
                    beginAtZero: true
                },
            },
            responsive: true,
            maintainAspectRatio: false,
        };
        const emptyStatePlugin = {
            id: 'emptyStateMonthlyMoves',
            afterDraw: (chart) => {
                if (!hasData) {
                    const { ctx, width, height } = chart;
                    ctx.save();
                    ctx.textAlign = 'center';
                    ctx.textBaseline = 'middle';
                    ctx.font = '500 14px system-ui, -apple-system, sans-serif';
                    ctx.fillStyle = '#94a3b8';
                    ctx.fillText('No stock movements recorded', width / 2, height / 2);
                    ctx.restore();
                }
            }
        };
        this.moveChartInstance = new Chart(ctx, {
            type: "line",
            data: data,
            options: options,
            plugins: [emptyStatePlugin]
        });
    }
    async render_product_categ_analysis() {
        var self = this
        const data = await this.orm.call('product.template', "get_product_location_analysis", [])
        var location = this.ProductLocation();
        if (location) {
            location.innerHTML = '';
            const entries = Object.entries((data && data.location_name) || {});
            if (entries.length === 0) {
                const option = document.createElement("option");
                option.value = "";
                option.textContent = "No locations available";
                location.appendChild(option);
            } else {
                var k = 0;
                entries.forEach(([key, value]) => {
                    const option = document.createElement("option");
                    option.id = key;
                    option.value = data.location_id[k];
                    option.textContent = value;
                    if (k == 0) {
                        option.selected = true;
                    }
                    location.appendChild(option);
                    k++;
                });
            }
        }
    }

    /**
     * Handle location selection change.
     *
     * Renders a bar chart showing product
     * quantities per selected location.
     */
    async onchange_location_selection() {
        if (this.locationChartInstance) {
            this.locationChartInstance.destroy();
            this.locationChartInstance = null;
        }
        var locationElement = this.ProductLocation();
        var option = locationElement ? locationElement.value : null;
        var ctx = this.ProductQtyChart();
        if (!ctx) return;

        let result = { products: [], quantity: [] };
        if (option) {
            result = await this.orm.call('product.template', "get_product_qty_by_loc", [option]);
        }
        var product_list = (result.products || []).map(p => {
            if (typeof p === 'object' && p !== null) {
                return p.en_US || Object.values(p)[0] || '';
            }
            return String(p || '');
        });
        const hasData = product_list.length > 0 && (result.quantity || []).some(val => Number(val) > 0);

        var data = {
            labels: product_list,
            datasets: [{
                label: 'Quantity On Hand',
                data: result.quantity || [],
                backgroundColor: '#0d9488',
                borderColor: '#0f766e',
                borderRadius: 6,
                borderWidth: 1
            }]
        };
        var options = {
            scales: {
                y: {
                    beginAtZero: true
                },
            },
            responsive: true,
            maintainAspectRatio: false,
        };
        const emptyStatePlugin = {
            id: 'emptyStateLocation',
            afterDraw: (chart) => {
                if (!hasData) {
                    const { ctx, width, height } = chart;
                    ctx.save();
                    ctx.textAlign = 'center';
                    ctx.textBaseline = 'middle';
                    ctx.font = '500 14px system-ui, -apple-system, sans-serif';
                    ctx.fillStyle = '#94a3b8';
                    ctx.fillText('No stock available in this location', width / 2, height / 2);
                    ctx.restore();
                }
            }
        };
        this.locationChartInstance = new Chart(ctx, {
            type: "bar",
            data: data,
            options: options,
            plugins: [emptyStatePlugin]
        });
    }
}

// Template and action registration
ProductDashboard.template = 'ProductDashboard'
registry.category("actions").add("product_dashboard_tag", ProductDashboard)