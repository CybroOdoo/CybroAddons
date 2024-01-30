/** @odoo-module **/
import { registry } from "@web/core/registry";
import { _t } from "@web/core/l10n/translation";
import { Component } from "@odoo/owl";
import { onWillStart, onMounted, useState, useRef } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";
export class ProductDashboard extends Component{
    setup(){
        super.setup(...arguments);
        this.orm = useService("orm");
        this.TopSaleChart = useRef("top_sale_chart")
        this.TopPurchaseChart = useRef("top_purchase_chart")
        this.ProductChart = useRef("product_graph")
        this.ProductQtyChart = useRef("product_qty")
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
    // fetch data to the tiles
        var result = await this.orm.call( 'product.template', "get_data",[])
        this.state.product_templates = result['product_templates']
        this.state.variants_count = result['product_variants']
        this.state.products_storable = result['storable']
        this.state.product_consumable = result['consumable']
        this.state.product_service = result['service']
        this.state.product_categ = result['category']
        this.state.product_pricelist = result['price_list']
        this.state.product_attribute = result['product_attribute']
    }
    async render_top_sold_product() {
     // To view the top sale products in the chart
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
        //options
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
        //create Chart class object
        var chart = new Chart(ctx, {
            type: "pie",
            data: data,
            options: options
        });
    }
    async render_top_purchase_product() {
    // To view the top purchase products in the chart
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
        //options
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
        //create Chart class object
        var chart = new Chart(ctx, {
            type: "doughnut",
            data: data,
            options: options
        });
    }
    async render_year_chart() {
    // For adding the last 5 years in the selection filed
        var self = this
        const data = await this.orm.call( 'product.template', "get_years",[])
        for (var year in data) {
            $('#year_selection').append('<option id="'+data[year]+'" value="'+data[year]+'">'+data[year]+'</option>')
        }
    }
    async render_monthly_chart() {
    // For listing the total products to filter the chart based on products
        var self = this
        const data = await this.orm.call( 'product.template', "get_products",[])
        var k = 0;
        Object.entries(data.product_name).forEach(([key, value]) => {
            if(k == 0){
                $('#prod_selection').append('<option id="'+key+'" value="'+data.product_id[k]+'" selected="selected">'+value+'</option>')
                k++;
            }else{
                $('#prod_selection').append('<option id="'+key+'" value="'+data.product_id[k]+'">'+value+'</option>')
                k++;
            }
        });
    }
    async onchange_prod_selection() {
    /* The filter is based on changes in products, displaying monthly
       product movements*/
        if (this.state.move_chart.length != 0) {
            this.state.move_chart.forEach((item)=> {
                item.destroy()
            });
        }
        var option = $("#prod_selection").val();
        var year = $("#year_selection").val();
        var ctx = this.ProductChart.el;
        const result = await this.orm.call('product.template', "get_prod_details", [option, year])
        var name = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
        var data = {
            labels: name,//x axis
            datasets: [{
                label: 'Purchase Order Total', // Name the series
                data: result.count, // Specify the data values array
                backgroundColor: '#0000ff',
                borderColor: '#0000ff',
                barPercentage: 0.5,
                barThickness: 6,
                maxBarThickness: 8,
                minBarLength: 0,
                borderWidth: 1, // Specify bar border width
                type: 'line', // Set this data to a line chart
                fill: false
            },]
        }
        var options = {
            scales: {
                y: {
                    beginAtZero: true
                },
            },
            responsive: true, // Instruct chart js to respond nicely.
            maintainAspectRatio: false, // Add to prevent default behaviour of full-width/height
        }
        var chart = new Chart(ctx, {
            type: "line",
            data: data,
            options: options
        });
        this.state.move_chart.push(chart)
    }
    async render_product_categ_analysis() {
    /* For listing the whole locations in the inventory in the*/
        var self = this
        const data = await this.orm.call( 'product.template', "get_product_location_analysis",[])
        var k = 0;
        Object.entries(data.location_name).forEach(([key, value]) => {
            if(k == 0){
                $('#product_location_selection').append('<option id="'+key+'" value="'+data.location_id[k]+'" selected="selected">'+value+'</option>')
                k++;
            }else{
                $('#product_location_selection').append('<option id="'+key+'" value="'+data.location_id[k]+'">'+value+'</option>')
                k++;
            }
        });
    }
    async onchange_location_selection() {
    /* The filter is based on changes in location, products based on the location */
        if (this.state.location_chart.length != 0) {
            this.state.location_chart.forEach((item)=> {
                item.destroy()
            });
        }
        var option = $("#product_location_selection" ).val();
        var ctx = this.ProductQtyChart.el;
        const result = await this.orm.call( 'product.template', "get_product_qty_by_loc", [option])
        var product_list = []
        for (var product in result.products) {
            product_list.push(result.products[product]['en_US'])
        }
        var data = {
            labels: product_list,
            datasets:  [{
                label: 'Count', // Name the series
                data: result.quantity, // Specify the data values array
                backgroundColor: '#ac3973',
                borderColor: '#ac3973',
                barPercentage: 0.5,
                barThickness: 6,
                maxBarThickness: 8,
                minBarLength: 0,
                borderWidth: 1, // Specify bar border width
                type: 'bar', // Set this data to a line chart
                fill: false
            }]
        }
        var options = {
            scales: {
                y: {
                    beginAtZero: true
                },
            },
            responsive: true, // Instruct chart js to respond nicely.
            maintainAspectRatio: false, // Add to prevent default behaviour of full-width/height
        }
        var chart = new Chart(ctx, {
            type: "bar",
            data: data,
            options: options
        });
        this.state.location_chart.push(chart)
    }
}
ProductDashboard.template = 'ProductDashboard'
registry.category("actions").add("product_dashboard_tag", ProductDashboard)
