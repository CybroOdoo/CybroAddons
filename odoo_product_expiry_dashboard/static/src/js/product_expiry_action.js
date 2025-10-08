/** @odoo-module */
import { registry } from "@web/core/registry"
import rpc from 'web.rpc';
const { Component, onWillStart, useState } = owl;
const actionRegistry = registry.category("actions");
var session = require('web.session');

export class ProductExpiryDashboard extends Component {
    setup() {
        super.setup(...arguments);
        this.state = useState({
            data: null,
            charts:[]
        })
        onWillStart(async () => {
          await this.fetch_products_expiry()
          await this.product_expired_today()
          await this.get_today_expire_products()
          await this.get_today_expire_products_category()
          await this.near_exp_products()
          await this.near_exp_category()
          await this.get_expire_product_location()
          await this.get_expire_product_warehouse()
          await this.render_expired_products_graph()
          await this.expiry_by_category()
        });
    }
//    Filter products based on the specified start and end dates.
    async filter_date(ev) {
        // Get the start and end dates selected by the user from input fields.
        var start_date = $("#start_date").val();
        var end_date = $("#end_date").val();
        if (this.state.charts.length != 0) {
            this.state.charts.forEach((item)=> {
                item.destroy()
            });
        }
        // Fetch and display products that fall within the specified date range.
        await this.fetch_products_expiry(start_date, end_date);
        await this.near_exp_products(start_date, end_date);
        await this.near_exp_category(start_date, end_date);
        await this.get_expire_product_location(start_date, end_date);
        await this.get_expire_product_warehouse(start_date, end_date);
        await this.render_expired_products_graph(start_date, end_date);
        await this.expiry_by_category(start_date, end_date);
    }
    fetch_products_expiry(start_date, end_date) {
        // Remove existing elements before updating the product expiry counts.
        $("#one_day").remove();
        $("#seven_day").remove();
        $("#thirty_day").remove();
        $("#one_twenty_day").remove();
        var self = this;
        // Prepare the date dictionary to pass as an argument in the RPC query.
        var date_dict = { 'start_date': start_date, 'end_date': end_date };
        // Send an RPC query to fetch product expiry data from the server.
        rpc.query({
            model: 'stock.lot',
            method: 'get_product_expiry',
            args: [date_dict, session.user_context.allowed_company_ids]
        }).then(function(result) {
            self.state.data = result
            var seven_day = result[0]['counts'] + result[1]['counts'];
            // Update the HTML elements to display the product counts for different expiry periods.
            $(".one-day").append('<center>'
                + '<span style="font-size: xxx-large;" id="one_day">' + result[0]['counts'] + '</span>'
                + '</center>');
            $(".seven-day").append('<center>'
                + '<span style="font-size: xxx-large;" id="seven_day">' + seven_day + '</span>'
                + '</center>');
            $(".thirty-day").append('<center>'
                + '<span style="font-size: xxx-large;" id="thirty_day">' + result[2]['counts'] + '</span>'
                + '</center>');
            $(".one-twenty-day").append('<center>'
                + '<span style="font-size: xxx-large;" id="one_twenty_day">' + result[3]['counts'] + '</span>'
                + '</center>');
        });
    }
//  Fetches the count of products that have expired today using an
//  RPC query and updates the HTML element to display the count.
    product_expired_today() {
        // Send an RPC query to fetch the count of products that have expired today.
        rpc.query({
            model: 'stock.lot',
            method: 'get_product_expired_today',
            args: [session.user_context.allowed_company_ids]
        }).then(function (result) {
            // Update the HTML element to display the count of products expired today.
            $('.product_expired_heading').append('<p style="font-size: 38px;margin-top: -10px;">' + result + '</p>');

        });
    }
//  Fetches the list of products that have expired today
    click_expired_today() {
        var self = this;
        rpc.query({
            model: 'stock.lot',
            method: 'get_today_expire',
        }).then(function (result) {
            var id = []
            for( var data in result['id']){
                id.push(parseInt(result['id'][data]))
            }
            // Perform the action to display products that have expired on the current day.
            self.env.services['action'].doAction({
                name: "Products Expired Today",
                type: 'ir.actions.act_window',
                res_model: 'stock.lot',
                views: [[false, 'tree'], [false, 'form']],
                domain: [['id', 'in', id]],
                target: 'current',
                context: {
                'create': false
                    }
            });
        });
    }
//  Fetches the list of products that have expired within 1 day(tomorrow)
    one_day_click() {
        // Perform the action to display products that are expiring in one day with negative product quantities.
        this.env.services['action'].doAction({
            name: "Expiry Tomorrow",
            type: 'ir.actions.act_window',
            res_model: 'stock.lot',
            views: [[false, 'tree'], [false, 'form']],
            domain: [['id', 'in', this.state.data[0]['one_day']]],
            target: 'current',
            context: {
                'create': false
            }
        });
    }
//  Fetches the list of products that have expired with in 7days
    seven_day_click() {
        const ids = [...this.state.data[1]['seven_day'], ...this.state.data[0]['one_day']]
        // Perform the action to display products that are expiring within the seven-day range.
        this.env.services['action'].doAction({
            name: "Expiry in Seven Days",
            type: 'ir.actions.act_window',
            res_model: 'stock.lot',
            views: [[false, 'tree'], [false, 'form']],
            domain: [['id', 'in', ids]],
            target: 'current',
            context: {
                'create': false
            }
        });
    }
//  Fetches the list of products that have expired in 30 days
    thirty_day_click() {
        const ids = [...this.state.data[2]['thirty_day']]
        // Perform the action to display products that are expiring within the thirty-day range.
        this.env.services['action'].doAction({
            name: "Expiry in Thirty Days",
            type: 'ir.actions.act_window',
            res_model: 'stock.lot',
            views: [[false, 'tree'], [false, 'form']],
            domain: [['id', 'in', ids]],
            target: 'current',
            context: {
                'create': false
            }
        });
    }
//  Fetches the list of products that have expired in 120 days
    one_twenty_day_click() {
        const ids = [...this.state.data[3]['one_twenty_day']]
        // Perform the action to display products that are expiring within the one hundred twenty-day range.
        this.env.services['action'].doAction({
            name: "Expiry in One Twenty Days",
            type: 'ir.actions.act_window',
            res_model: 'stock.lot',
            views: [[false, 'tree'], [false, 'form']],
            domain: [['id', 'in', ids]],
            target: 'current',
            context: {
                'create': false
            }
        });
    }
//  Line Chart for Products Expired Today
    get_today_expire_products() {
        // Initialize arrays to hold product warehouse names and their corresponding quantities.
        var expire_product_name = [];
        var expire_product_qty = [];
        // Send an RPC query to fetch data about products that are about to expire, categorized by their warehouses, from the server.
        rpc.query({
            model: 'stock.lot',
            method: 'get_today_expire',
        }).then(function (result) {
            for( var data in result['name']){
                expire_product_name.push(result['name'][data])
                expire_product_qty.push(parseInt(result['qty'][data]))
            }
            // Render the bar chart using Chart.js.
            const ctx = $('#today_expire_products');
            new Chart(ctx, {
                type: 'line',
                data: {
                    labels: expire_product_name,
                    datasets: [{
                        label: 'Quantity',
                        data: expire_product_qty,
                        borderWidth: 1
                    }]
                },
                options: {
                    plugins: {
                        legend: {
                            position: 'bottom',
                        },
                        title: {
                            display: true,
                        }
                    }
                }
            });
        });
    }
//  Bar chart for Products Expired Today by Category
    get_today_expire_products_category() {
        // Initialize arrays to hold product warehouse names and their corresponding quantities.
        var expire_product_categ_name = [];
        var expire_product_qty = [];
        // Send an RPC query to fetch data about products that are about to expire, categorized by their warehouses, from the server.
        rpc.query({
            model: 'stock.lot',
            method: 'get_today_expire',
        }).then(function (result) {
            // Extract product warehouse names and their corresponding quantities from the fetched data.
            for( var data in result['categ']){
                for (var key in result['categ'][data]) {
                    if (result['categ'][data].hasOwnProperty(key)) {
                        var value = result['categ'][data][key];
                    }
                    expire_product_categ_name.push(key)
                    expire_product_qty.push(parseInt(value))
                }
            }
            // Render the bar chart using Chart.js.
            const ctx = $('#today_expire_products_category');
            new Chart(ctx, {
                type: 'bar',
                data: {
                    labels: expire_product_categ_name,
                    datasets: [{
                        label: 'Quantity',
                        data: expire_product_qty,
                        backgroundColor: [
                            'rgba(75, 192, 192, 0.2)',
                            'rgba(54, 162, 235, 0.2)',
                            'rgba(153, 102, 255, 0.2)',
                            'rgba(201, 203, 207, 0.2)',
                            'rgba(255, 99, 132, 0.2)',
                            'rgba(255, 159, 64, 0.2)',
                            'rgba(255, 205, 86, 0.2)',
                        ],
                        borderColor: [
                            'rgb(75, 192, 192)',
                            'rgb(54, 162, 235)',
                            'rgb(153, 102, 255)',
                            'rgb(201, 203, 207)',
                            'rgb(255, 99, 132)',
                            'rgb(255, 159, 64)',
                            'rgb(255, 205, 86)',
                        ],
                        borderWidth: 1
                    }]
                },
                options: {
                    plugins: {
                        legend: {
                            position: 'bottom',
                        },
                        title: {
                            display: true,
                        }
                    }
                }
            });
        });
    }
//  chart for products expire in 7 days
    near_exp_products(start_date, end_date) {
        var self = this;
        // Initialize arrays to hold product names and their corresponding near expiry quantities.
        var product_array = [];
        var nearby_expire_qty = [];
        // Prepare the date dictionary to pass as an argument in the RPC query.
        var date_dict = { 'start_date': start_date, 'end_date': end_date };
        // Send an RPC query to fetch data about products that are near their expiry date from the server.
        rpc.query({
            model: 'stock.lot',
            method: 'get_near_expiry_product',
            args: [date_dict],
        }).then(function (result) {
            // Extract product names and their corresponding near expiry quantities from the fetched data.
            $.each(result, function (index, name) {
                product_array.push(index);
                nearby_expire_qty.push(name);
            });
            // Render the bar chart using Chart.js.
            const ctx = $('#nearby_expire_product');
            self.state.charts.push(new Chart(ctx, {
                type: 'bar',
                data: {
                    labels: product_array,
                    datasets: [{
                        label: 'Quantity',
                        data: nearby_expire_qty,
                        backgroundColor: [
                            'rgba(255, 205, 86, 0.2)',
                            'rgba(75, 192, 192, 0.2)',
                            'rgba(54, 162, 235, 0.2)',
                            'rgba(153, 102, 255, 0.2)',
                            'rgba(201, 203, 207, 0.2)',
                            'rgba(255, 99, 132, 0.2)',
                            'rgba(255, 159, 64, 0.2)',
                        ],
                        borderColor: [
                            'rgb(255, 205, 86)',
                            'rgb(75, 192, 192)',
                            'rgb(54, 162, 235)',
                            'rgb(153, 102, 255)',
                            'rgb(201, 203, 207)',
                            'rgb(255, 99, 132)',
                            'rgb(255, 159, 64)',
                        ],
                        borderWidth: 1
                    }]
                },
                options: {
                    plugins: {
                        legend: {
                            position: 'bottom',
                        },
                        title: {
                            display: true,
                        }
                    }
                }
            }));
        });
    }
//  Chart for products category expire in 7 days
    near_exp_category(start_date, end_date) {
        var self = this;
        // Initialize arrays to hold product category names and their corresponding near expiry quantities.
        var product_category_array = [];
        var nearby_expire_qty = [];
        // Prepare the date dictionary to pass as an argument in the RPC query.
        var date_dict = { 'start_date': start_date, 'end_date': end_date };
        // Send an RPC query to fetch data about products that are near their expiry date, categorized by their product categories.
        rpc.query({
            model: 'stock.lot',
            method: 'get_near_expiry_category',
            args: [date_dict],
        }).then(function (result) {
            // Extract product category names and their corresponding near expiry quantities from the fetched data.
            $.each(result, function (index, name) {
                product_category_array.push(index);
                nearby_expire_qty.push(name);
            });
            // Render the bar chart using Chart.js.
            const ctx = $('#nearby_expire_catg');
            self.state.charts.push(new Chart(ctx, {
                type: 'bar',
                data: {
                    labels: product_category_array,
                    datasets: [{
                        label: 'Quantity',
                        data: nearby_expire_qty,
                        backgroundColor: [
                            'rgba(255, 159, 64, 0.2)',
                            'rgba(255, 205, 86, 0.2)',
                            'rgba(75, 192, 192, 0.2)',
                            'rgba(54, 162, 235, 0.2)',
                            'rgba(153, 102, 255, 0.2)',
                            'rgba(201, 203, 207, 0.2)',
                            'rgba(255, 99, 132, 0.2)',
                        ],
                        borderWidth: 1
                    }]
                },
                options: {
                    plugins: {
                        legend: {
                            position: 'bottom',
                        },
                        title: {
                            display: true,
                        }
                    }
                }
            }));
        });
    }
//  Expiry in Seven Days
    get_expire_product_location(start_date, end_date) {
        var self = this;
        // Initialize arrays to hold product location names and their corresponding quantities.
        var product_location_array = [];
        var nearby_expire_qty = [];
        // Prepare the date dictionary to pass as an argument in the RPC query.
        var date_dict = { 'start_date': start_date, 'end_date': end_date };
        // Send an RPC query to fetch data about products that are about to expire, categorized by their locations, from the server.
        rpc.query({
            model: 'stock.lot',
            method: 'get_expire_product_location',
            args: [date_dict],
        }).then(function (result) {
            // Extract product location names and their corresponding quantities from the fetched data.
            $.each(result, function (index, name) {
                product_location_array.push(index);
                nearby_expire_qty.push(name);
            });
            // Render the pie chart using Chart.js.
            const ctx = $('#nearby_expire_location');
            self.state.charts.push(new Chart(ctx, {
                type: 'pie',
                data: {
                    labels: product_location_array,
                    datasets: [{
                        label: 'Quantity',
                        data: nearby_expire_qty,
                        borderWidth: 1
                    }]
                },
                options: {
                    plugins: {
                        legend: {
                            position: 'bottom',
                        },
                        title: {
                            display: true,
                        }
                    }
                }
            }));
        });
    }
//  Products by Warehouse Expire in 7 Days
    get_expire_product_warehouse(start_date, end_date) {
        var self = this;
        // Initialize arrays to hold product warehouse names and their corresponding quantities.
        var product_warehouse_array = [];
        var nearby_expire_qty = [];
        // Prepare the date dictionary to pass as an argument in the RPC query.
        var date_dict = { 'start_date': start_date, 'end_date': end_date };
        // Send an RPC query to fetch data about products that are about to expire, categorized by their warehouses, from the server.
        rpc.query({
            model: 'stock.lot',
            method: 'get_expire_product_warehouse',
            args: [date_dict],
        }).then(function (result) {
            // Extract product warehouse names and their corresponding quantities from the fetched data.
            $.each(result, function (index, name) {
                product_warehouse_array.push(index);
                nearby_expire_qty.push(name);
            });
            // Render the bar chart using Chart.js.
            const ctx = $('#nearby_expire_warehouse');
            self.state.charts.push(new Chart(ctx, {
                type: 'doughnut',
                data: {
                    labels: product_warehouse_array,
                    datasets: [{
                        label: 'Quantity',
                        data: nearby_expire_qty,
                        backgroundColor: [
                            'rgba(75, 192, 192, 0.2)',
                            'rgba(54, 162, 235, 0.2)',
                            'rgba(153, 102, 255, 0.2)',
                            'rgba(201, 203, 207, 0.2)',
                            'rgba(255, 99, 132, 0.2)',
                            'rgba(255, 159, 64, 0.2)',
                            'rgba(255, 205, 86, 0.2)',
                        ],
                        borderColor: [
                            'rgb(75, 192, 192)',
                            'rgb(54, 162, 235)',
                            'rgb(153, 102, 255)',
                            'rgb(201, 203, 207)',
                            'rgb(255, 99, 132)',
                            'rgb(255, 159, 64)',
                            'rgb(255, 205, 86)',
                        ],
                        borderWidth: 1
                    }]
                },
                options: {
                    plugins: {
                        legend: {
                            position: 'bottom',
                        },
                        title: {
                            display: true,
                        }
                    }
                }
            }));
        });
    }
//  Expired Products
    render_expired_products_graph(start_date, end_date) {
        // Check if a chart with the ID 'expired_product_count' already exists and destroy it if it does.
        let chartStatus = Chart.getChart('expired_product_count');
        if (chartStatus !== undefined) {
            chartStatus.destroy();
        }
        // Initialize arrays to hold product names and their corresponding expired quantities.
        var product_array = [];
        var expired_qty_array = [];
        // Prepare the date dictionary to pass as an argument in the RPC query.
        var date_dict = { 'start_date': start_date, 'end_date': end_date };
        // Send an RPC query to fetch data about expired products from the server.
        let data = rpc.query({
            model: 'stock.lot',
            method: 'get_expired_product',
            args: [date_dict,]
        }).then(function (result) {
            // Extract product names and their corresponding expired quantities from the fetched data.
            $.each(result, function (index, name) {
                product_array.push(index);
                expired_qty_array.push(name);
            });
            // Render the pie chart using Chart.js.
            const ctx = $('#expired_product_count');
            new Chart(ctx, {
                type: 'pie',
                data: {
                    labels: product_array,
                    datasets: [{
                        label: 'Quantity',
                        data: expired_qty_array,
                        borderWidth: 1
                    }]
                },
                options: {
                    plugins: {
                        legend: {
                            position: 'bottom',
                        },
                        title: {
                            display: true,
                        }
                    }
                }
            });
        });
    }
//  Expired Products by Category
    expiry_by_category(start_date, end_date) {
        // Check if a chart with the ID 'expired_product_category_count' already exists and destroy it if it does.
        let chartStatus = Chart.getChart('expired_product_category_count');
        if (chartStatus !== undefined) {
            chartStatus.destroy();
        }
        // Initialize arrays to hold product category names and their corresponding expired quantities.
        var product_category_array = [];
        var expired_qty_array = [];
        // Prepare the date dictionary to pass as an argument in the RPC query.
        var date_dict = { 'start_date': start_date, 'end_date': end_date };
        // Send an RPC query to fetch data about expired products categorized by their product categories from the server.
        rpc.query({
            model: 'stock.lot',
            method: 'get_product_expiry_by_category',
            args: [date_dict,session.user_context.allowed_company_ids]
        }).then(function (result) {
            // Extract product category names and their corresponding expired quantities from the fetched data.
            $.each(result, function (index, name) {
                product_category_array.push(index);
                expired_qty_array.push(name);
            });
            // Render the bar chart using Chart.js.
            const ctx = $('#expired_product_category_count');
            new Chart(ctx, {
                type: 'polarArea',
                data: {
                    labels: product_category_array,
                    datasets: [{
                        label: 'Quantity',
                        data: expired_qty_array,
                        borderWidth: 1
                    }]
                },
                options: {
                    plugins: {
                        legend: {
                            position: 'bottom',
                        },
                        title: {
                            display: true,
                        }
                    }
                }
            });
        });
    }
}
ProductExpiryDashboard.template = "ProductExpiryDashboard"
actionRegistry.add('product_expiry', ProductExpiryDashboard);
