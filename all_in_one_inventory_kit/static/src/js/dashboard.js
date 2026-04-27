/** @odoo-module **/
import { registry } from "@web/core/registry";
import { Component, useState, useRef } from "@odoo/owl";
import { session } from "@web/session";
import { onWillStart,onMounted } from "@odoo/owl";
import {loadCSS, loadJS} from "@web/core/assets";
import { rpc } from "@web/core/network/rpc";

var result_3;
export class InventoryDashboard extends Component{
        setup()  {
            super.setup();
                this.rpc = this.env.services.rpc
                this.pro_info = useRef('pro_info')
                this.canvas = useRef('canvas')
                this.stock_moves = useRef('stock_moves')
                this.product_move_table = useRef('product_move_table')
                this.category_table = useRef('category_table')
                this.product_category = useRef('product_category')
                this.graphs = useRef('graphs')
                this.out_of_stock_table = useRef('out_of_stock_table')
                this.location_table = useRef('location_table')
                this.product_move_graph = useRef('product_move_graph')
                this.product_move_selection = useRef('product_move_selection')
                this.stock_move_table = useRef('stock_move_table')
                this.canvaspie = useRef('canvaspie')
                this.graph_details_table = useRef('graph_details_table')
                this.operation_type_table = useRef('operation_type_table')
                this.set = useRef('set')
                this.operation = useRef('operation')
                this.dashboards_templates = ['InventoryTiles', 'ProductSaleBarGraph'];
                onMounted(this.onMounted);
        }
	 /**
     * Event handler for the 'onMounted' event.
     * Renders various components and charts after fetching data.
     */
	async onMounted() {
		// Render other components after fetching data
		var self = this;
        self.render_graphs();
	}
     /** Render the dashboard graphs */
        render_graphs(){
            var self = this;
            self.render_operation_tile();
            self.render_stock_moves();
            self.render_product_move_graph_this_month();
            self.render_product_category();
            self.render_storage_location();
            self.render_out_of_stock_graph();
        }
        // Append the dashboard cards
        render_operation_tile() {
            var self = this;
            var def1 = rpc('/get_operation_types')
            .then(function(result) {
                var operation_types = result[0];
                var late = result[1];
                var waiting = result[2];
                var backorder = result[4];
                var r = 1;
                var g = 0;
                result_3 = result[3];
                const colors = ["red", "blue", "green", "orange", "purple", "steel", "rebecca", "brown", "pink", "grey", "black"];
                // Iterate over operation types and append the data to the HTML
                var types = self.set.el
                Object.entries(operation_types).forEach(([key, value]) => {
                    r++;
                    var result_1 = key;
                    var result_2 = value;
                     var div = document.createElement('div');
                     div.style.display = "contents";
                        div.innerHTML = `<div class="col-sm-12 col-md-6 col-lg-3" id="${result_1}" t-on-click="() => this.onclick_tiles()">
                            <div class="dashboard-card dashboard-card--border-top dashboard-card--border-top-${colors[g]}">
                                <div class="dashboard-card__details">
                                    <span class="dashboard-card__title">${result_3[result_1]}</span>
                                    <span class="count-container">${result_2}</span>
                                </div>
                                <ul class="dashboard-card__stats"></ul>
                            </div>
                        </div>`;
                        types.appendChild(div);
                     g++;
                     // Append stats for late, waiting, and backorder
                     if (key in late) {
                        // Find the dashboard card stats element by ID
                        const dashStats = div.querySelector('.dashboard-card__stats');
                        // Create the <li> element
                        const li = document.createElement('li');
                        li.className = "dashboard-card__stat_late";
                        li.id = result_1;
                        li.setAttribute('t-on-click', '(e) => this.onclick_late_status(e)');
                        // Create the inner HTML for the <li>
                        li.innerHTML = `
                            <div class="d-flex justify-content-between align-items-center text-dark text-decoration-none">
                                <div class="dashboard-card__stat-title_late">Late</div>
                                <div class="dashboard-card__stat-count_late">${late[key]}</div>
                            </div>`;
                        // Append the <li> to the dashboard card stats <ul>
                        dashStats.appendChild(li);
                    }
                    if (key in waiting) {
                        // Find the dashboard card stats element by ID
                        const dashStats = div.querySelector('.dashboard-card__stats');
                        // Create the <li> element
                        const li = document.createElement('li');
                        li.className = "dashboard-card__stat_waiting";
                        li.id = result_1;
                        li.setAttribute('t-on-click', '(e) => this.onclick_waiting_status(e)');
                        // Create the inner HTML for the <li>
                        li.innerHTML = `
                            <div class="d-flex justify-content-between align-items-center text-dark text-decoration-none">
                                <div class="dashboard-card__stat-title_waiting">Waiting</div>
                                <div class="dashboard-card__stat-count_waiting">${waiting[key]}</div>
                            </div>`;
                        // Append the <li> to the dashboard card stats <ul>
                        dashStats.appendChild(li);
                    }
                    if (key in backorder) {
                        // Find the dashboard card stats element by ID
                        const dashStats = div.querySelector('.dashboard-card__stats');
                        // Create the <li> element
                        const li = document.createElement('li');
                        li.className = "dashboard-card__stat_backorder";
                        li.id = result_1;
                        li.setAttribute('t-on-click', '(e) => this.onclick_backorders_status(e)');
                        // Set the inner HTML for the <li>
                        li.innerHTML = `
                            <div class="d-flex justify-content-between align-items-center text-dark text-decoration-none">
                                <div class="dashboard-card__stat-title_back">Backorder</div>
                                <div class="dashboard-card__stat-count_backorder">${backorder[key]}</div>
                            </div>`;
                        // Append the <li> to the dashboard card stats <ul>
                        dashStats.appendChild(li);
                    }
                });
                // Now handle the chart
                var ctx = self.operation.el // Make sure we are getting the first DOM element, which is the <canvas>
                // Check if the element exists and is a canvas
                if (ctx && ctx.getContext) {
                    var name = Object.values(result[3]); // Add data values to array
                    var count = Object.values(result[0]);
                    var j = 0;
                    // Populate the table
                    var operation_type = self.operation_type_table.el
                    for (var c in count) {
                        var row = document.createElement('tr');
                        row.innerHTML = `<td>${name[j]}</td><td class="location_table_value">${count[c]}</td>`;
                        operation_type.appendChild(row);
                        j++;
                    }
                    self.operation_type_table.el.classList.add('d-none');
                    // Define the chart data
                    var data = {
                        labels: name, // x-axis
                        datasets: [{
                            label: 'Count', // Name the series
                            data: count, // Specify the data values array
                            backgroundColor: [
                                "#003f5c", "#2f4b7c", "#f95d6a", "#665191", "#d45087",
                                "#ff7c43", "#ffa600", "#a05195", "#6d5c16", "#CCCCFF",
                            ],
                            borderColor: [
                                "#003f5c", "#2f4b7c", "#f95d6a", "#665191", "#d45087",
                                "#ff7c43", "#ffa600", "#a05195", "#6d5c16", "#CCCCFF",
                            ],
                            borderWidth: 1, // Specify bar border width
                            barPercentage: 0.5,
                            barThickness: 6,
                            maxBarThickness: 8,
                            minBarLength: 0,
                            type: 'bar', // Set this data to a bar chart
                            fill: false
                        }]
                    };
                    // Define chart options
                    var options = {
                        scales: {
                            y: {
                                beginAtZero: true
                            }
                        },
                        responsive: true, // Instruct Chart.js to respond nicely.
                        maintainAspectRatio: false // Prevent default behavior of full-width/height.
                    };
                    // Create the chart
                    var chart = new Chart(ctx.getContext('2d'), {
                        type: 'bar',
                        data: data,
                        options: options
                    });
                } else {
                    console.error("Canvas element not found or context cannot be acquired.");
                }
                });
            }
        /** Top ten bar graph */
        render_top_product_bar_graph(){
            var self = this
            rpc('/get_the_top_products')
            .then(function (result) {
                var ctx = self.canvas.el;
                var products = result.products // Add data values to array
                var count = result.count;
                var j = 0;
                var graph_details_table = self.graph_details_table.el
                Object.entries(result.count).forEach(([key, value]) => {
                    var row = document.createElement('tr');
                    row.innerHTML = `<td>${products[j]}</td><td class="location_table_value">${value}</td>`;
                    graph_details_table.appendChild(row);
                    j++;
                    });
                self.graph_details_table.el.classList.add("d-none");
                var myChart = new Chart(ctx, {
                    type: 'bar',
                    data: {
                        labels: products,//x axis
                        datasets: [{
                            label: 'Count', // Name the series
                            data: count, // Specify the data values array
                            backgroundColor: [
                                "#003f5c",
                                "#2f4b7c",
                                "#f95d6a",
                                "#665191",
                                "#d45087",
                                "#ff7c43",
                                "#ffa600",
                                "#a05195",
                                "#6d5c16",
                                "#CCCCFF"
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
                                "#6d5c16",
                                "#CCCCFF"
                            ],
                            barPercentage: 0.5,
                            barThickness: 6,
                            maxBarThickness: 8,
                            minBarLength: 0,
                            borderWidth: 1, // Specify bar border width
                            type: 'bar', // Set this data to a line chart
                            fill: false
                        }]
                    },
                    options: {
                        scales: {
                            y: {
                                beginAtZero: true
                            },
                        },
                        responsive: true, // Instruct chart js to respond nicely.
                        maintainAspectRatio: false, // Add to prevent default behaviour of full-width/height
                    }//                                borderColor: '#66aecf',
                });
            });
        }
    /** Product categories doughnut graph */
        render_product_category(){
            var self = this
           rpc('/get_product_category')
                .then(function (result) {
                var ctx = self.product_category.el
                /** Define the data */
                var name = result.name /** Add data values to array */
                var count = result.count
                var j = 0;
                Object.entries(result.count).forEach(([key, value]) => {
                    self.category_table.el.append('<tr><td>'+name[j]+'</td><td>'+value+'</td></tr>')
                    j++;
                });
                self.category_table.el.classList.add("d-none");
                var myChart = new Chart(ctx, {
                    type: 'doughnut',
                    data: {
                        labels: name,/** x axis */
                        datasets: [{
                            label: 'Quantity Done', /** Name the series */
                            data: count, /** Specify the data values array */
                            backgroundColor: [
                                "#003f5c",
                                "#2f4b7c",
                                "#f95d6a",
                                "#665191",
                                "#d45087",
                                "#ff7c43",
                                "#ffa600",
                                "#a05195",
                                "#6d5c16",
                                "#CCCCFF"
                            ],
                            borderColor: [
                                "#003f5c",
                            ],
                            barPercentage: 0.5,
                            barThickness: 6,
                            maxBarThickness: 8,
                            minBarLength: 0,
                            borderWidth: 1, /** Specify bar border width */
                            type: 'doughnut', /** Set this data to a line chart */
                            fill: false
                        }]
                    },
                    options: {
                        scales: {
                            y: {
                                beginAtZero: true
                            },
                        },
                        responsive: true, /** Instruct chart js to respond nicely. */
                        maintainAspectRatio: false, /** Add to prevent default behaviour of full-width/height */
                    }
                });
            });
        }
        /** Product move line graph */
        render_product_move_graph_this_month(){
            var self = this
           rpc('/get_product_moves')
                .then(function (result) {
                var ctx = self.product_move_graph.el;
                var name = result[0].name // Add data values to array
                var count = result[0].count
                var category_name = result[1].category_name
                var category_id = result[1].category_id
                 var j = 0;
                 var k = 0;
                 var  selection = self.product_move_selection.el
                Object.entries(result[1].category_name).forEach(([key, value]) => {

                    if(k == 0){
                        var option = document.createElement('option');
                            option.id = key;  // Set the id attribute
                            option.value = category_id[k];  // Set the value attribute
                            option.textContent = value;
                            selection.appendChild(option);
                        k++;
                    }
                });
                var option = self.product_move_selection.el.value;
                self.product_move_table.el.classList.add("d-none");
                rpc('/product_move_by_category',{
                        args: option
                    }).then(function(result) {
                    var ctx = self.product_move_graph.el
                    var name = result.name
                    var count = result.count;
                    var j = 0;
                    var product_move = self.product_move_table.el
                    Object.entries(result.count).forEach(([key, value]) => {
                        var row = document.createElement('tr');
                            row.innerHTML = `<td>${name[j]}</td><td class="location_table_value">${value}</td>`;
                            product_move.appendChild(row);
                        j++;
                    });
                    self.product_move_table.el.classList.add("done");
                    var myChart = new Chart(ctx, {
                        type: 'line',
                    data: {
                        labels: name,//x axis
                        datasets: [{
                            label: 'Quantity Done', // Name the series
                            data: count, // Specify the data values array
                            backgroundColor: '#003f5c',
                            borderColor: '#003f5c',
                            barPercentage: 0.5,
                            barThickness: 6,
                            maxBarThickness: 8,
                            minBarLength: 0,
                            borderWidth: 1, // Specify bar border width
                            type: 'line', // Set this data to a line chart
                            fill: false
                        }]
                    },
                    options: {
                        scales: {
                            y: {
                                beginAtZero: true
                            },
                        },
                        responsive: true, // Instruct chart js to respond nicely.
                        maintainAspectRatio: false, // Add to prevent default behaviour of full-width/height
                    }
                    });
                });
            });
        }
    //    Stock moves pie graph
        render_stock_moves(){
            var self = this;
           rpc('/get_stock_moves')
               .then(function (result) {
                var ctx = self.stock_moves.el;
                var name = result.name
                var count = result.count;
                var j = 0;
                Object.entries(result.count).forEach(([key, value]) => {
                    self.stock_move_table.el.append('<tr><td>'+name[j]+'</td><td>'+value+'</td></tr>')
                            j++;
                    });
                self.stock_move_table.el.classList.add("d-none");
                var myChart = new Chart(ctx, {
                    type: 'pie',
                    data: {
                        labels: name,//x axis
                        datasets: [{
                            label: 'Count', // Name the series
                            data: count, // Specify the data values array
                            backgroundColor: [
                                "#003f5c",
                                "#2f4b7c",
                                "#f95d6a",
                                "#665191",
                                "#d45087",
                                "#ff7c43",
                                "#ffa600",
                                "#a05195",
                                "#6d5c16",
                                "#CCCCFF"
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
                                "#6d5c16",
                                "#CCCCFF"
                            ],
                            barPercentage: 0.5,
                            barThickness: 6,
                            maxBarThickness: 8,
                            minBarLength: 0,
                            borderWidth: 1, // Specify bar border width
                            type: 'pie', // Set this data to a line chart
                            fill: false
                        }]
                    },
                    options: {
                        scales: {
                            y: {
                                beginAtZero: true
                            },
                        },
                        responsive: true, // Instruct chart js to respond nicely.
                        maintainAspectRatio: false, // Add to prevent default behaviour of full-width/height
                    }
                });
            });
        }
        //  location-on hand table
        render_storage_location() {
            var self = this;
            rpc('/get_locations')
                .then(function (result) {
                    // Select the tbody with class 'storage'
                    var tbody = self.location_table.el.querySelector('tbody.storage');
                    if (tbody) {
                        tbody.innerHTML = '';  // Clear existing rows
                        // Loop through the result and append rows
                        Object.entries(result).forEach(([key, value]) => {
                            // Create a new row element
                            var row = document.createElement('tr');
                            row.innerHTML = `<td>${key}</td><td class="location_table_value">${value}</td>`;
                            tbody.appendChild(row);  // Append the row to the tbody
                        });
                    }
        })
    }
        //Out of stock graph
        render_out_of_stock_graph(){
            var self = this
            rpc('/get_out_of_stock')
                .then(function (result) {
                if (result) {
                self.graphs.el.append('<div class="year_to_date_graph_div col-sm-12 col-md-6 my-4">
                <div class="chart-container card-shadow" id="tiles"><div style="height: 20px; max-height: 20px;"><h2>Out of Stock Products</h2>
                <button class="btn_info" id="out_of_stock_info" title="Show Details"><i class="fa fa-ellipsis-v"></i></button>
                <table class="graph_details_table" t-ref="out_of_stock_table"><tr><th>Products</th><th>Out of Quantity</th>
                </tr></table>
                </div><hr/><div class="graph_canvas" style="margin-top: 30px;"><canvas id="out_of_stock_graph" height="500px" width="150px"/>
                </div></div></div>')
                var ctx = self.out_of_stock_table.el;
                var name = result.product_name // Add data values to array
                var count = result.total_quantity
                var j = 0;
                Object.entries(name).forEach(([key, value]) => {
                    self.out_of_stock_table.el.append('<tr><td>'+value+'</td><td>'+count[j]+'</td></tr>')
                    j++;
                });
                self.out_of_stock_table.el.classList.add('d-none')
                var myChart = new Chart(ctx, {
                    type: 'bar',
                    data: {
                        labels: name,//x axis
                        datasets: [{
                            label: 'Current Stock', // Name the series
                            data: count, // Specify the data values array
                            backgroundColor: '#003f5c',
                            borderColor: '#003f5c',
                            barPercentage: 0.5,
                            barThickness: 6,
                            maxBarThickness: 8,
                            minBarLength: 0,
                            borderWidth: 1, // Specify bar border width
                            type: 'bar', // Set this data to a line chart
                            fill: false
                        }]
                    },
                    options: {
                        scales: {
                            y: {
                                beginAtZero: true
                            },
                        },
                        responsive: true, // Instruct chart js to respond nicely.
                        maintainAspectRatio: false, // Add to prevent default behaviour of full-width/height
                    }
                });
                }
            });
        }
        //Dead stock graph
        render_dead_of_stock_graph(){
            var self = this
            rpc('/get_dead_of_stock')
               .then(function (result) {
                if (result) {
                    $('#graphs').append('<div class="year_to_date_graph_div col-sm-12 col-md-6 my-4">
                    <div class="chart-container card-shadow" id="tiles"><div style="height: 20px; max-height: 20px;"><h2>Dead Stock</h2>
                    <button class="btn_info" id="dead_stock_info" title="Show Details"><i class="fa fa-ellipsis-v"></i></button>
                    <table class="graph_details_table" id="dead_stock_table"><tr><th>Products</th><th>Dead Quantity</th>
                    </tr></table>
                    </div><hr/><div class="graph_canvas" style="margin-top: 30px;"><canvas id="dead_stock_graph" height="500px" width="150px"/>
                    </div></div></div>')
                    var ctx = $("#dead_stock_graph");
                    var name = result.product_name // Add data values to array
                    var count = result.total_quantity
                    var j = 0;
                    Object.entries(name).forEach(([key, value]) => {
                        $('#dead_stock_table').append('<tr><td>'+value+'</td><td>'+count[j]+'</td></tr>')
                        j++;
                    });
                    $('#dead_stock_table').hide();
                    var myChart = new Chart(ctx, {
                        type: 'line',
                        data: {
                            labels: name,//x axis
                            datasets: [{
                                label: 'Current Stock', // Name the series
                                data: count, // Specify the data values array
                                backgroundColor: '#003f5c',
                                borderColor: '#003f5c',
                                barPercentage: 0.5,
                                barThickness: 6,
                                maxBarThickness: 8,
                                minBarLength: 0,
                                borderWidth: 1, // Specify bar border width
                                type: 'line', // Set this data to a line chart
                                fill: false
                            }]
                        },
                        options: {
                            scales: {
                                y: {
                                    beginAtZero: true
                                },
                            },
                            responsive: true, // Instruct chart js to respond nicely.
                            maintainAspectRatio: false, // Add to prevent default behaviour of full-width/height
                        }
                    });
                }
            });
        }
    //Top product selection
        onclick_top_product_selection(events){
        console.log(events,'events')
            if (events == 'top_last_10_days'){
            var self = this
            rpc('/top_products_last_ten')
                .then(function (result) {
                var ctx = self.canvaspie.el
                // Define the data
                var products = result.products // Add data values to array
                var count = result.count;
                var j = 0;
                var prod_info =  self.graph_details_table.el
                var cells = prod_info.querySelectorAll('td');
                cells.forEach(function(cell) {
                    cell.remove();  // Remove each <td> element
                });
                Object.entries(result.count).forEach(([key, value]) => {
                    var row = document.createElement('tr');
                    row.innerHTML = `<td>${products[j]}</td><td class="product_moving_value">${value}</td>`;
                    prod_info.appendChild(row);
                    j++;
                    });
                prod_info.classList.add('d-none');
                var myChart = new Chart(ctx, {
                    type: 'bar',
                    data: {
                        labels: products,//x axis
                        datasets: [{
                            label: 'Count', // Name the series
                            data: count, // Specify the data values array
                            backgroundColor: [
                                "#003f5c",
                                "#2f4b7c",
                                "#f95d6a",
                                "#665191",
                                "#d45087",
                                "#ff7c43",
                                "#ffa600",
                                "#a05195",
                                "#6d5c16",
                                "#CCCCFF",
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
                                "#6d5c16",
                                "#CCCCFF",
                            ],
                            barPercentage: 0.5,
                            barThickness: 6,
                            maxBarThickness: 8,
                            minBarLength: 0,
                            borderWidth: 1, // Specify bar border width
                            type: 'bar', // Set this data to a line chart
                            fill: false
                        }]
                    },
                    options: {
                        scales: {
                            y: {
                                beginAtZero: true
                            },
                        },
                        responsive: true, // Instruct chart js to respond nicely.
                        maintainAspectRatio: false, // Add to prevent default behaviour of full-width/height
                    }
                });
            });
            }
            if (events == 'top_last_30_days'){
                var self = this;
                rpc('/top_products_last_thirty')
                .then(function (result) {
                var ctx = self.canvaspie.el
                console.log(result,'result')
                // Define the data
                var products = result.products // Add data values to array
                console.log(products,'products')
                var count = result.count;
                var j = 0;
                 var prod_info =  self.graph_details_table.el
                var cells = prod_info.querySelectorAll('td');
                cells.forEach(function(cell) {
                    cell.remove();  // Remove each <td> element
                });
                Object.entries(result.count).forEach(([key, value]) => {
                    var row = document.createElement('tr');
                    row.innerHTML = `<td>${products[j]}</td><td class="location_table_value">${value}</td>`;
                    prod_info.appendChild(row);
                    j++;
                    });
                prod_info.classList.add('d-none');
                var myChart = new Chart(ctx, {
                    type: 'bar',
                    data: {
                        labels: products,//x axis
                        datasets: [{
                            label: 'Count', // Name the series
                            data: count, // Specify the data values array
                            backgroundColor: [
                                "#003f5c",
                                "#2f4b7c",
                                "#f95d6a",
                                "#665191",
                                "#d45087",
                                "#ff7c43",
                                "#ffa600",
                                "#a05195",
                                "#6d5c16",
                                "#CCCCFF"
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
                                "#6d5c16",
                                "#CCCCFF"
                            ],
                            barPercentage: 0.5,
                            barThickness: 6,
                            maxBarThickness: 8,
                            minBarLength: 0,
                            borderWidth: 1, // Specify bar border width
                            type: 'bar', // Set this data to a line chart
                            fill: false
                        }]
                    },
                    options: {
                        scales: {
                            y: {
                                beginAtZero: true
                            },
                        },
                        responsive: true, // Instruct chart js to respond nicely.
                        maintainAspectRatio: false, // Add to prevent default behaviour of full-width/height
                    }
                });
            });
            }
            if (events == 'top_last_3_month'){
                var self = this;
                rpc('/top_products_last_three_months')
                .then(function (result) {
                var ctx = self.canvaspie.el
                var products = result.products // Add data values to array
                var count = result.count;
                var j = 0;
                var prod_info =  self.graph_details_table.el
                var cells = prod_info.querySelectorAll('td');
                cells.forEach(function(cell) {
                    cell.remove();  // Remove each <td> element
                });
                Object.entries(result.count).forEach(([key, value]) => {
                    var row = document.createElement('tr');
                    row.innerHTML = `<td>${products[j]}</td><td class="location_table_value">${value}</td>`;
                    prod_info.appendChild(row);
                    j++;
                    });
                prod_info.classList.add('d-none');
                var myChart = new Chart(ctx, {
                    type: 'bar',
                    data: {
                        labels: products,//x axis
                        datasets: [{
                            label: 'Count', // Name the series
                            data: count, // Specify the data values array
                            backgroundColor: [
                                "#003f5c",
                                "#2f4b7c",
                                "#f95d6a",
                                "#665191",
                                "#d45087",
                                "#ff7c43",
                                "#ffa600",
                                "#a05195",
                                "#6d5c16",
                                "#CCCCFF"
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
                                "#6d5c16",
                                "#CCCCFF"
                            ],
                            barPercentage: 0.5,
                            barThickness: 6,
                            maxBarThickness: 8,
                            minBarLength: 0,
                            borderWidth: 1, // Specify bar border width
                            type: 'bar', // Set this data to a line chart
                            fill: false
                        }]
                    },
                    options: {
                        scales: {
                            y: {
                                beginAtZero: true
                            },
                        },
                        responsive: true, // Instruct chart js to respond nicely.
                        maintainAspectRatio: false, // Add to prevent default behaviour of full-width/height
                    }
                });
            });
            }
            if (events == 'top_last_year'){
                var self = this;
                rpc('/top_products_last_year')
                .then(function (result) {
                var ctx = self.canvaspie.el
                var products = result.products // Add data values to array
                var count = result.count;
                var j = 0;
                 var prod_info =  self.graph_details_table.el
                var cells = prod_info.querySelectorAll('td');
                cells.forEach(function(cell) {
                    cell.remove();  // Remove each <td> element
                });
                Object.entries(result.count).forEach(([key, value]) => {
                    var row = document.createElement('tr');
                    row.innerHTML = `<td>${products[j]}</td><td class="location_table_value">${value}</td>`;
                    prod_info.appendChild(row);
                    j++;
                    });
                prod_info.classList.add('d-none');
                var myChart = new Chart(ctx, {
                    type: 'bar',
                    data: {
                        labels: products,//x axis
                        datasets: [{
                            label: 'Count', // Name the series
                            data: count, // Specify the data values array
                            backgroundColor: [
                                "#003f5c",
                                "#2f4b7c",
                                "#f95d6a",
                                "#665191",
                                "#d45087",
                                "#ff7c43",
                                "#ffa600",
                                "#a05195",
                                "#6d5c16",
                                "#CCCCFF"
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
                                "#6d5c16",
                                "#CCCCFF"
                            ],
                            barPercentage: 0.5,
                            barThickness: 6,
                            maxBarThickness: 8,
                            minBarLength: 0,
                            borderWidth: 1, // Specify bar border width
                            type: 'bar', // Set this data to a line chart
                            fill: false
                        }]
                    },
                    options: {
                        scales: {
                            y: {
                                beginAtZero: true
                            },
                        },
                        responsive: true, // Instruct chart js to respond nicely.
                        maintainAspectRatio: false, // Add to prevent default behaviour of full-width/height
                    }
                });
            });
            }
        }
    //    stock moves this_mont,last_year change
        async onclick_stock_moves_selection(ev){
            var self = this;
            if (ev == 'last_10_days'){
                 var s = await rpc('/stock_move_last_ten_days').then(function(result) {
                    var ctx = self.stock_moves.el;
                    var name = result.name
                    var count = result.count;
                    var stock_move =  self.stock_move_table.el
                    var cells = stock_move.querySelectorAll('td');
                    cells.forEach(function(cell) {
                        cell.remove();  // Remove each <td> element
                    });
                    var j = 0;
                    Object.entries(result.count).forEach(([key, value]) => {
                        var row = document.createElement('tr');
                        row.innerHTML = `<td>${name[j]}</td><td class="location_table_value">${value}</td>`;
                        stock_move.appendChild(row);
                        j++;
                        });
                    stock_move.classList.add('d-none')
                    var myChart = new Chart(ctx, {
                        type: 'pie',
                        data: {
                            labels: name,//x axis
                            datasets: [{
                                label: 'Count', // Name the series
                                data: count, // Specify the data values array
                                backgroundColor: [
                                    "#003f5c",
                                    "#2f4b7c",
                                    "#f95d6a",
                                    "#665191",
                                    "#d45087",
                                    "#ff7c43",
                                    "#ffa600",
                                    "#a05195",
                                    "#6d5c16",
                                    "#CCCCFF"
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
                                    "#6d5c16",
                                    "#CCCCFF"
                                ],
                                barPercentage: 0.5,
                                barThickness: 6,
                                maxBarThickness: 8,
                                minBarLength: 0,
                                borderWidth: 1, // Specify bar border width
                                type: 'pie', // Set this data to a line chart
                                fill: false
                            }]
                        },
                        options: {
                            scales: {
                                y: {
                                    beginAtZero: true
                                },
                            },
                            responsive: true, // Instruct chart js to respond nicely.
                            maintainAspectRatio: false, // Add to prevent default behaviour of full-width/height
                        }
                    });

                });
            }
            if (ev == 'this_month'){
                rpc('/this_month').then(function(result) {
                    var ctx = self.stock_moves.el
                    var name = result.name
                    var count = result.count;
                    var j = 0;
                    var stock_move =  self.stock_move_table.el
                    var cells = stock_move.querySelectorAll('td');
                    cells.forEach(function(cell) {
                        cell.remove();  // Remove each <td> element
                    });
                    Object.entries(result.count).forEach(([key, value]) => {
                        var row = document.createElement('tr');
                        row.innerHTML = `<td>${name[j]}</td><td class="location_table_value">${value}</td>`;
                        stock_move.appendChild(row);
                    j++;
                    });
                stock_move.classList.add('d-none')
                    var myChart = new Chart(ctx, {
                        type: 'pie',
                        data: {
                            labels: name,//x axis
                            datasets: [{
                                label: 'Count', // Name the series
                                data: count, // Specify the data values array
                                backgroundColor: [
                                    "#003f5c",
                                    "#2f4b7c",
                                    "#f95d6a",
                                    "#665191",
                                    "#d45087",
                                    "#ff7c43",
                                    "#ffa600",
                                    "#a05195",
                                    "#6d5c16",
                                    "#CCCCFF"
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
                                    "#6d5c16",
                                    "#CCCCFF"
                                ],
                                barPercentage: 0.5,
                                barThickness: 6,
                                maxBarThickness: 8,
                                minBarLength: 0,
                                borderWidth: 1, // Specify bar border width
                                type: 'pie', // Set this data to a line chart
                                fill: false
                            }]
                        },
                        options: {
                            scales: {
                                y: {
                                    beginAtZero: true
                                },
                            },
                            responsive: true, // Instruct chart js to respond nicely.
                            maintainAspectRatio: false, // Add to prevent default behaviour of full-width/height
                        }
                    });
                });
            }
            if (ev == 'last_3_month'){
                rpc('/last_three_month').then(function(result) {
                    var ctx = self.stock_moves.el
                    var name = result.name
                    var count = result.count;
                    var j = 0;
                    var stock_move =  self.stock_move_table.el
                    var cells = stock_move.querySelectorAll('td');
                    cells.forEach(function(cell) {
                        cell.remove();  // Remove each <td> element
                    });
                    Object.entries(result.count).forEach(([key, value]) => {
                         var row = document.createElement('tr');
                        row.innerHTML = `<td>${name[j]}</td><td class="location_table_value">${value}</td>`;
                        stock_move.appendChild(row);
                    j++;
                    });
                stock_move.classList.add('d-none')
                    var myChart = new Chart(ctx, {
                        type: 'pie',
                        data: {
                            labels: name,//x axis
                            datasets: [{
                                label: 'Count', // Name the series
                                data: count, // Specify the data values array
                                backgroundColor: [
                                    "#003f5c",
                                    "#2f4b7c",
                                    "#f95d6a",
                                    "#665191",
                                    "#d45087",
                                    "#ff7c43",
                                    "#ffa600",
                                    "#a05195",
                                    "#6d5c16",
                                    "#CCCCFF"
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
                                    "#6d5c16",
                                    "#CCCCFF"
                                ],
                                barPercentage: 0.5,
                                barThickness: 6,
                                maxBarThickness: 8,
                                minBarLength: 0,
                                borderWidth: 1, // Specify bar border width
                                type: 'pie', // Set this data to a line chart
                                fill: false
                            }]
                        },
                        options: {
                            scales: {
                                y: {
                                    beginAtZero: true
                                },
                            },
                            responsive: true, // Instruct chart js to respond nicely.
                            maintainAspectRatio: false, // Add to prevent default behaviour of full-width/height
                        }
                    });
                });
            }
            else if (ev == 'last_year'){
                rpc('/last_year').then(function(result) {
                var ctx = self.stock_moves.el
                    var name = result.name
                    var count = result.count;
                    var j = 0;
                    var stock_move =  self.stock_move_table.el
                    var cells = stock_move.querySelectorAll('td');
                    cells.forEach(function(cell) {
                        cell.remove();  // Remove each <td> element
                    });
                    Object.entries(result.count).forEach(([key, value]) => {
                         var row = document.createElement('tr');
                        row.innerHTML = `<td>${name[j]}</td><td class="location_table_value">${value}</td>`;
                        stock_move.appendChild(row);
                    j++;
                    });
                stock_move.classList.add('d-none')
                    var myChart = new Chart(ctx, {
                        type: 'pie',
                        data: {
                            labels: name,//x axis
                            datasets: [{
                                label: 'Count', // Name the series
                                data: count, // Specify the data values array
                                backgroundColor: [
                                    "#003f5c",
                                    "#2f4b7c",
                                    "#f95d6a",
                                    "#665191",
                                    "#d45087",
                                    "#ff7c43",
                                    "#ffa600",
                                    "#a05195",
                                    "#6d5c16",
                                    "#CCCCFF"
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
                                    "#6d5c16",
                                    "#CCCCFF"
                                ],
                                barPercentage: 0.5,
                                barThickness: 6,
                                maxBarThickness: 8,
                                minBarLength: 0,
                                borderWidth: 1, // Specify bar border width
                                type: 'pie', // Set this data to a line chart
                                fill: false
                            }]
                        },
                        options: {
                            scales: {
                                y: {
                                    beginAtZero: true
                                },
                            },
                            responsive: true, // Instruct chart js to respond nicely.
                            maintainAspectRatio: false, // Add to prevent default behaviour of full-width/height
                        }
                    });
                });
            }
        }
//    product move selection
        onclick_product_moves_selection(events){
            var option = $(events.target).val();
                var self = this
                rpc('/product_move_by_category',{
                    args: option
                }).then(function(result) {
                    var ctx = $("#product_move_graph");
                    var name = result.name
                    var count = result.count;
                    var j = 0;
                    $('#product_move_table td').remove();
                    Object.entries(result.count).forEach(([key, value]) => {
                        $('#product_move_table').append('<tr><td>'+name[j]+'</td><td>'+value+'</td></tr>')
                    j++;
                    });
                    $('#product_move_table').hide();
                    var myChart = new Chart(ctx, {
                        type: 'line',
                    data: {
                        labels: name,//x axis
                        datasets: [{
                            label: 'Quantity Done', // Name the series
                            data: count, // Specify the data values array
                            backgroundColor: '#003f5c',
                            borderColor: '#003f5c',
                            barPercentage: 0.5,
                            barThickness: 6,
                            maxBarThickness: 8,
                            minBarLength: 0,
                            borderWidth: 1, // Specify bar border width
                            type: 'line', // Set this data to a line chart
                            fill: false
                        }]
                    },
                    options: {
                        scales: {
                            y: {
                                beginAtZero: true
                            },
                        },
                        responsive: true, // Instruct chart js to respond nicely.
                        maintainAspectRatio: false, // Add to prevent default behaviour of full-width/height
                    }
                    });
                });
        }
    //    Tile click
        onclick_tiles() {
            var id = parseInt(this.$(f.currentTarget).attr('id'));
            var options = {
                on_reverse_breadcrumb: this.on_reverse_breadcrumb,
            };
            this.do_action({
                name: _t(result_3[this.$(f.currentTarget).attr('id')]),
                type: 'ir.actions.act_window',
                res_model: 'stock.picking',
                view_mode: 'list,form,calendar',
                views: [[false, 'list'],[false, 'form']],
                domain: [['picking_type_id', '=', id]],
                target: 'current',
            }, options);
        }
    //    Tile late status onclick
        onclick_late_status(f) {
            f.stopPropagation();
            var id = parseInt(this.$(f.currentTarget).attr('id'));
            var v ='/Late'
            var options = {
                on_reverse_breadcrumb: this.on_reverse_breadcrumb,
            };
            this.do_action({
                name: _t(result_3[id]+v),
                type: 'ir.actions.act_window',
                res_model: 'stock.picking',
                view_mode: 'list,form,calendar',
                views: [[false, 'list'],[false, 'form']],
                domain: [['picking_type_id', '=', id],['state', 'in', ['assigned', 'waiting', 'confirmed']],['scheduled_date', '<=', moment().format('YYYY-MM-DD')],],
                target: 'current',
            }, options)
        }
   //    Tile waiting status onclick
        onclick_waiting_status(f) {
            f.stopPropagation();
            var id = parseInt(this.$(f.currentTarget).attr('id'));
            var options = {
                on_reverse_breadcrumb: this.on_reverse_breadcrumb,
            };
            this.do_action({
                name: _t(result_3[id]+'/Waiting'),
                type: 'ir.actions.act_window',
                res_model: 'stock.picking',
                view_mode: 'list,form,calendar',
                views: [[false, 'list'],[false, 'form']],
                domain: [['picking_type_id', '=', id],['state', '=', 'confirmed']],
                target: 'current',
            }, options)
        }
    //    Tile backorder status onclick
        onclick_backorders_status(f) {
            f.stopPropagation();
            var id = parseInt(this.$(f.currentTarget).attr('id'));
            var options = {
                on_reverse_breadcrumb: this.on_reverse_breadcrumb,
            };
            this.do_action({
                name: _t(result_3[id]+'/Backorders'),
                type: 'ir.actions.act_window',
                res_model: 'stock.picking',
                view_mode: 'list,form,calendar',
                views: [[false, 'list'],[false, 'form']],
                domain: [['picking_type_id', '=', id],['backorder_id', '!=', false]],
                target: 'current',
            }, options)
        }
   //    Top ten product show details button click
        onclick_top_product_info(f) {
            var x = this.graph_details_table.el
            if (x.classList.contains("d-none")) {
                x.style.display = "block";  // Show the element
                x.classList.remove("d-none");
              } else {
                x.style.display = "none";
                x.classList.add("d-none");
            }
        }
    //    Product category graph show details button click
        onclick_pro_cate_info(f) {
            var x = document.getElementById("category_table");
            if (x.style.display === "none") {
                x.style.display = "block";
              } else {
                x.style.display = "none";
            }
        }
    //    Stock moves show details button click
        onclick_location_info(f) {
            var x = document.getElementById("location_table");
            if (x.style.display === "none") {
                x.style.display = "block";
              } else {
                x.style.display = "none";
            }
        }
    //    Operation types table show details button click
        onclick_operation_type_info(f) {
            var x = this.operation_type_table.el
            if (x.classList.contains("d-none")) {
                x.style.display = "block";
                x.classList.remove("d-none")
              } else {
                x.style.display = "none";
                x.classList.add("d-none")
            }
        }
        //    Dead stock table show details button click
        onclick_dead_stock_info(f) {
            var x = document.getElementById("dead_stock_table");
            if (x.style.display === "none") {
                x.style.display = "block";
              } else {
                x.style.display = "none";
            }
        }
        //    Out of stock table show details button click
        onclick_out_of_stock_info(f) {
            var x = document.getElementById("out_of_stock_table");
            if (x.style.display === "none") {
                x.style.display = "block";
              } else {
                x.style.display = "none";
            }
        }
//    Click product move info
        onclick_product_move_info(f) {
            var x = this.product_move_table.el;
            if (x.classList.contains("d-none")) {
                x.style.display = "block";  // Show the element
                x.classList.remove("d-none");
              } else {
                x.style.display = "none";
                x.classList.add("d-none");
            }
        }
//    Click stock move info
        onclick_stock_move_info(f) {
            var x = document.getElementById("stock_move_table");
            if (x.style.display === "none") {
                x.style.display = "block";
              } else {
                x.style.display = "none";
            }
        }
}
InventoryDashboard.template = 'Dashboard';
registry.category("actions").add("inventory_dashboard_tag", InventoryDashboard );
