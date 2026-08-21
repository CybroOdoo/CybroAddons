/** @odoo-module **/
import { registry } from "@web/core/registry";
import { Component, onWillStart, onMounted, useState, useRef } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";
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
        this.TopSaleChart = useRef("top_sale_chart")
        this.TopPurchaseChart = useRef("top_purchase_chart")
        this.ProductChart = useRef("product_graph")
        this.ProductQtyChart = useRef("product_qty")
        this.YearSelection = useRef("year-selection")
        this.ProductSelection = useRef("product-selection")
        this.ProductLocation = useRef("product-location")
        this.state = useState({
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
        var result = await this.orm.call( 'product.template', "get_data",[])
        this.state.product_templates = result['product_templates']
        this.state.variants_count = result['product_variants']
        this.state.products_storable = result['combo']
        this.state.product_consumable = result['goods']
        this.state.product_service = result['service']
        this.state.product_categ = result['category']
        this.state.product_pricelist = result['price_list']
        this.state.product_attribute = result['product_attribute']
    }
    async render_top_sold_product() {
        var self = this
        var ctx = this.TopSaleChart.el;
        const arrays = await this.orm.call(
        'product.template', "get_top_sale_data",[])
        var data = {
            labels : arrays[1],
            datasets: [{
                label: "",
                data: arrays[0],
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
            },]
        };
        var options = {
            responsive: true,
            title: false,
            legend: {
                display: true,
                position: "right",
                labels: {
                    fontColor: "#333",
                    fontSize: 16
                }
            },
            scales: {
                yAxes: [{
                    gridLines: {
                        color: "rgba(0, 0, 0, 0)",
                        display: false,
                    },
                    ticks: {
                        min: 0,
                        display: false,
                    }
                }]
            }
        };
        var chart = new Chart(ctx, {
            type: "pie",
            data: data,
            options: options
        });
    }
    async render_top_purchase_product() {
        var self = this
        var ctx = this.TopPurchaseChart.el;
        const arrays = await this.orm.call( 'product.template', "get_top_purchase_data",[])
        var data = {
            labels : arrays[1],
            datasets: [{
                label: "",
                data: arrays[0],
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
            },]
        };
        var options = {
            responsive: true,
            title: false,
            legend: {
                display: true,
                position: "right",
                labels: {
                    fontColor: "#333",
                    fontSize: 16
                }
            },
            scales: {
                yAxes: [{
                    gridLines: {
                        color: "rgba(0, 0, 0, 0)",
                        display: false,
                    },
                    ticks: {
                        min: 0,
                        display: false,
                    }
                }]
            }
        };
        var chart = new Chart(ctx, {
            type: "doughnut",
            data: data,
            options: options
        });
    }
    async render_year_chart() {
        var self = this
        const data = await this.orm.call( 'product.template', "get_years",[])
        const select = this.YearSelection.el || this.YearSelection.getEl?.();
        if (select) {
            data.forEach(year => {
                const option = document.createElement("option");
                option.value = year;
                option.textContent = year;
                select.appendChild(option);
            });
        } else {
            console.error("Year selection element not found.");
        }
    }
    async render_monthly_chart() {
        var self = this
        const data = await this.orm.call( 'product.template', "get_products",[])
        const products = this.ProductSelection.el || this.ProductSelection.getEl?.();
        if (products) {
            products.innerHTML = '';
            var k = 0;
            Object.entries(data.product_name).forEach(([key, value]) => {
                const option = document.createElement("option");
                option.value = data.product_id[k];
                option.textContent = value;
                if (k == 0) {
                    option.selected = true;
                }
                products.appendChild(option);
                k++;
            });
        } else {
            console.error("Product selection element not found or is not a <select> element.");
        }
    }
    async onchange_prod_selection() {
        if (this.state.move_chart.length != 0) {
            this.state.move_chart.forEach((item)=> {
                item.destroy()
            });
        }
        var productElement = this.ProductSelection.el || this.ProductSelection.getEl?.();
        var option = productElement ? productElement.value : null;
        var yearElement = this.YearSelection.el || this.YearSelection.getEl?.();
        var year = yearElement ? yearElement.value : null;
        var ctx = this.ProductChart.el;
        const result = await this.orm.call('product.template', "get_prod_details", [option, year])
        var name = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
        var data = {
            labels: name,
            datasets: [{
                label: 'Purchase Order Total',
                data: result.count,
                backgroundColor: '#0000ff',
                borderColor: '#0000ff',
                barPercentage: 0.5,
                barThickness: 6,
                maxBarThickness: 8,
                minBarLength: 0,
                borderWidth: 1,
                type: 'line',
                fill: false
            },]
        }
        var options = {
            scales: {
                y: {
                    beginAtZero: true
                },
            },
            responsive: true,
            maintainAspectRatio: false,
        }
        var chart = new Chart(ctx, {
            type: "line",
            data: data,
            options: options
        });
        this.state.move_chart.push(chart)
    }
    async render_product_categ_analysis() {
        var self = this
        const data = await this.orm.call( 'product.template', "get_product_location_analysis",[])
        var location = this.ProductLocation.el || this.ProductLocation.getEl?.();
        if (location) {
            location.innerHTML = '';
            var k = 0;
            Object.entries(data.location_name).forEach(([key, value]) => {
                const option = document.createElement("option");
                option.id = key
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

    /**
     * Handle location selection change.
     *
     * Renders a bar chart showing product
     * quantities per selected location.
     */
    async onchange_location_selection() {
        if (this.state.location_chart.length != 0) {
            this.state.location_chart.forEach((item)=> {
                item.destroy()
            });
        }
        var locationElement = this.ProductLocation.el || this.ProductSelection.getEl?.();
        var option = locationElement ? locationElement.value : null;
        var ctx = this.ProductQtyChart.el;
        const result = await this.orm.call('product.template', "get_product_qty_by_loc", [option])
        var product_list = []
        for (var product in result.products) {
            product_list.push(result.products[product]['en_US'])
        }
        var data = {
            labels: product_list,
            datasets:  [{
                label: 'Count',
                data: result.quantity,
                backgroundColor: '#ac3973',
                borderColor: '#ac3973',
                barPercentage: 0.5,
                barThickness: 6,
                maxBarThickness: 8,
                minBarLength: 0,
                borderWidth: 1,
                type: 'bar',
                fill: false
            }]
        }
        var options = {
            scales: {
                y: {
                    beginAtZero: true
                },
            },
            responsive: true,
            maintainAspectRatio: false,
        }
        var chart = new Chart(ctx, {
            type: "bar",
            data: data,
            options: options
        });
        this.state.location_chart.push(chart)
    }
}

// Template and action registration
ProductDashboard.template = 'ProductDashboard'
registry.category("actions").add("product_dashboard_tag", ProductDashboard)
