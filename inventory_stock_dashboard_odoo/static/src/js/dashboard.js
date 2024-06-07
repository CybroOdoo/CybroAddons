/** @odoo-module **/
import { registry } from "@web/core/registry";
import { onWillStart, onMounted, useState, useRef } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";
const actionRegistry = registry.category("actions");
import { _t } from "@web/core/l10n/translation";
const { DateTime } = luxon;
var op_type;
/* This class represents dashboard in Inventory. */
class Dashboard extends owl.Component{
    setup() {
        this.orm = useService('orm')
        this.rootRef = useRef('root')
        this.state = useState({
            countDictionary : [],
            op_types: [],
            operations: [],
            colors: [],
            late_status: [],
            waiting_status: [],
            backorder_status: [],
            MoveData: [],
            operationDict: [],
            category: [],
            categCountDict: [],
            categName: [],
            location_data: [],
            monthly_stock: [],
            monthly_stock_count: [],
            out_stock: [],
            out_stock_count: [],
            dead_stock_name: [],
        });
        // When the component is about to start, fetch data in tiles
        onWillStart(async () => {
            this.props.title = 'Dashboard';
        });
        // When the component is mounted, render various charts
        onMounted(async () => {
            await this.render_graphs();
        });
    }
    render_graphs(){
        this.render_operation_tile();
        this.render_top_product_bar_graph();
        this.render_stock_moves();
        this.render_product_move_graph_this_month();
        this.render_product_category();
        this.render_storage_location();
        this.render_out_of_stock_graph();
        this.render_dead_of_stock_graph();
    }
    // Fetch data operation type tiles and graphs
    render_operation_tile(){
        var result =  this.orm.call('stock.picking', 'get_operation_types', []
        ).then( (result) => {
            op_type = result[3];
            const colors = ["red", "blue","green","orange","purple","steel","rebecca","brown","pink","grey","black"];
            this.state.op_types = result[0];
            this.state.operations = result[3];
            this.state.colors = colors;
            this.state.late_status = result[1];
            this.state.waiting_status = result[2];
            this.state.backorder_status = result[4];
            var ctx = this.rootRef.el.querySelector("#operation")
            var name = Object.values(result[3])
            var count = Object.values(result[0])
            var operationDict = {}
            for (var i = 0; i < name.length; i++) {
                var operation = name[i];
                var operationCount = count[i];
                operationDict[operation] = operationCount;
            }
            this.state.operationDict = operationDict
            this.rootRef.el.querySelector('#operation_type_table').style.display = 'none';
            var myChart = new Chart(ctx, {
                type: 'bar',
                data: {
                    labels: name,
                    datasets: [{
                        label: 'Count',
                        data: count,
                        backgroundColor: [
                            "#003f5c","#2f4b7c","#f95d6a","#665191",
                            "#d45087","#ff7c43","#ffa600","#a05195",
                            "#6d5c16","#CCCCFF"
                        ],
                        borderColor: [
                            "#003f5c","#2f4b7c","#f95d6a","#665191",
                            "#d45087","#ff7c43","#ffa600","#a05195",
                            "#6d5c16","#CCCCFF"
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
    // Top moving products bar graph
    async render_top_product_bar_graph(){
        const ctx = this.rootRef.el.querySelector("#canvaspie");
        await this.orm.call("stock.move", "get_the_top_products", []
        ).then( (result) => {
            var products = result.products
            var count = result.count;
            var countDictionary = {};
            for (var i = 0; i < products.length; i++) {
                var product = products[i];
                var productCount = count[i];
                countDictionary[product] = productCount;
            }
            this.state.countDictionary = countDictionary;
            this.rootRef.el.querySelector("#pro_info").style.display = 'none';
            var myChart = new Chart(ctx, {
                type: 'bar',
                data: {
                    labels: products,
                    datasets: [{
                        label: 'Count',
                        data: count,
                        backgroundColor: [
                            "#003f5c","#2f4b7c","#f95d6a","#665191",
                            "#d45087","#ff7c43","#ffa600","#a05195",
                            "#6d5c16","#CCCCFF"
                        ],
                        borderColor: [
                            "#003f5c","#2f4b7c","#f95d6a","#665191",
                            "#d45087","#ff7c43","#ffa600","#a05195",
                            "#6d5c16","#CCCCFF"
                        ],
                        barPercentage: 0.5,
                        barThickness: 6,
                        maxBarThickness: 8,
                        minBarLength: 0,
                        borderWidth: 1,
                        type: 'bar',
                        fill: false
                    }]
                },
                options: {
                    scales: {
                        y: {
                            beginAtZero: true
                        },
                    },
                    responsive: true,
                    maintainAspectRatio: false,
                }
            });
        });
    }
    // Stock moves pie graph
    async render_stock_moves(){
        this.orm.call("stock.move", "get_stock_moves", []
        ).then( (result) => {
            var name = result.name
            var count = result.count;
            var stockMoveDict = {}
            for (var i = 0; i < name.length; i++) {
                var location = name[i];
                var stockCount = count[i];
                stockMoveDict[location] = stockCount;
            }
            this.state.MoveData = stockMoveDict;
            this.rootRef.el.querySelector('#stock_move_table').style.display = 'none';
            var ctx = this.rootRef.el.querySelector("#stock_moves");
            var myChart = new Chart(ctx, {
                type: 'pie',
                data: {
                    labels: name,
                    datasets: [{
                        label: 'Count',
                        data: count,
                        backgroundColor: [
                            "#003f5c","#2f4b7c","#f95d6a","#665191",
                            "#d45087","#ff7c43","#ffa600","#a05195",
                            "#6d5c16","#CCCCFF"
                        ],
                        borderColor: [
                            "#003f5c","#2f4b7c","#f95d6a","#665191",
                            "#d45087","#ff7c43","#ffa600","#a05195",
                            "#6d5c16","#CCCCFF"
                        ],
                        barPercentage: 0.5,
                        barThickness: 6,
                        maxBarThickness: 8,
                        minBarLength: 0,
                        borderWidth: 1,
                        type: 'pie',
                        fill: false
                    }]
                },
                options: {
                    scales: {
                        y: {
                            beginAtZero: true
                        },
                    },
                    responsive: true,
                    maintainAspectRatio: false,
                }
            });
        });
    }
    // Product move line graph
    render_product_move_graph_this_month(){
        this.orm.call("stock.move.line", "get_product_moves", []
        ).then((result) => {
            var ctx = this.rootRef.el.querySelector("#product_move_graph");
            var name = result[0].name
            var count = result[0].count
            var category_name = result[1].category_name
            var category_id = result[1].category_id
            this.state.category = category_name
            this.state.categoryId = category_id
            var option = this.state.categoryId[0]
            this.rootRef.el.querySelector('#product_move_table').style.display = 'none';
            this.orm.call("stock.move.line", "product_move_by_category", [option]
                ).then( (result) => {
                    var ctx = this.rootRef.el.querySelector("#product_move_graph");
                    var name = result.name
                    var count = result.count;
                    this.state.monthly_stock = name
                    this.state.monthly_stock_count = count
                    this.rootRef.el.querySelector("#product_move_table").style.display = 'none';
                    var myChart = new Chart(ctx, {
                        type: 'line',
                    data: {
                        labels: name,
                        datasets: [{
                            label: 'Quantity Done',
                            data: count,
                            backgroundColor: '#003f5c',
                            borderColor: '#003f5c',
                            barPercentage: 0.5,
                            barThickness: 6,
                            maxBarThickness: 8,
                            minBarLength: 0,
                            borderWidth: 1,
                            type: 'line',
                            fill: false
                        }]
                    },
                    options: {
                        scales: {
                            y: {
                                beginAtZero: true
                            },
                        },
                        responsive: true,
                        maintainAspectRatio: false,
                    }
                });
            });
        });
    }
    // Product categories doughnut graph
    render_product_category(){
        this.orm.call("stock.picking", "get_product_category", []).
        then((result) => {
            var ctx = this.rootRef.el.querySelector("#product_category");
            var name = result.name
            var count = result.count
            var categCountDict = {}
            this.state.categCountDict = name;
            this.state.categName = count;
            this.rootRef.el.querySelector("#category_table").style.display = 'none';
            var myChart = new Chart(ctx, {
                type: 'doughnut',
                data: {
                    labels: name,
                    datasets: [{
                        label: 'Quantity Done',
                        data: count,
                        backgroundColor: [
                            "#003f5c","#2f4b7c","#f95d6a","#665191",
                            "#d45087","#ff7c43","#ffa600","#a05195",
                            "#6d5c16","#CCCCFF"
                        ],
                        borderColor: [
                            "#003f5c",
                        ],
                        barPercentage: 0.5,
                        barThickness: 6,
                        maxBarThickness: 8,
                        minBarLength: 0,
                        borderWidth: 1,
                        type: 'doughnut',
                        fill: false
                    }]
                },
                options: {
                    scales: {
                        y: {
                            beginAtZero: true
                        },
                    },
                    responsive: true,
                    maintainAspectRatio: false,
                }
            });
        });
    }
    // Location-on hand table
    render_storage_location(){
        this.orm.call("stock.picking", "get_locations",
        ).then((result) => {
            this.state.location_data = result
        });
    }
    // Dead stock graph
    render_dead_of_stock_graph(){
        this.orm.call("stock.move", "get_dead_of_stock",[]
        ).then( (result) => {
            if (result) {
                this.rootRef.el.querySelector("#dead_stock").style.display = 'block';
                var ctx = this.rootRef.el.querySelector("#dead_stock_graph");
                var name = result.product_name
                var count = result.total_quantity
                this.state.dead_stock_name = name
                this.state.dead_stock_count = count
                this.rootRef.el.querySelector('#dead_stock_table').style.display = 'none';
                var myChart = new Chart(ctx, {
                    type: 'line',
                    data: {
                        labels: name,
                        datasets: [{
                            label: 'Current Stock',
                            data: count,
                            backgroundColor: '#003f5c',
                            borderColor: '#003f5c',
                            barPercentage: 0.5,
                            barThickness: 6,
                            maxBarThickness: 8,
                            minBarLength: 0,
                            borderWidth: 1,
                            type: 'line',
                            fill: false
                        }]
                    },
                    options: {
                        scales: {
                            y: {
                                beginAtZero: true
                            },
                        },
                        responsive: true,
                        maintainAspectRatio: false,
                    }
                });
            }
            else{
                this.rootRef.el.querySelector('#dead_stock').style.display = 'none';
            }
        });
    }
    // Out of stock graph
    render_out_of_stock_graph(){
        this.orm.call("stock.quant", "get_out_of_stock",[]
        ).then( (result) => {
            if (result) {
                var ctx = this.rootRef.el.querySelector("#out_of_stock_graph");
                var name = result.product_name
                var count = result.total_quantity
                this.state.out_stock = name
                this.state.out_stock_count = count
                this.rootRef.el.querySelector("#out_of_stock").style.display = 'block';
                this.rootRef.el.querySelector("#out_of_stock_table").style.display = 'none';
                var myChart = new Chart(ctx, {
                    type: 'bar',
                    data: {
                        labels: name,
                        datasets: [{
                            label: 'Current Stock',
                            data: count,
                            backgroundColor: '#003f5c',
                            borderColor: '#003f5c',
                            barPercentage: 0.5,
                            barThickness: 6,
                            maxBarThickness: 8,
                            minBarLength: 0,
                            borderWidth: 1,
                            type: 'bar',
                            fill: false
                        }]
                    },
                    options: {
                        scales: {
                            y: {
                                beginAtZero: true
                            },
                        },
                        responsive: true,
                        maintainAspectRatio: false,
                    }
                });
            }
            else{
                this.rootRef.el.querySelector("#out_of_stock").style.display = 'none';
            }
        });
    }
    // Top ten products details button click
    async onclick_top_product_info(event) {
        var pro_info = this.rootRef.el.querySelector("#pro_info");
        if (pro_info.style.display === "none") {
            pro_info.style.display = 'block';
        } else {
            pro_info.style.display = 'none';
        }
    }
    // Stock move details button click
    onclick_stock_move_info() {
    var move_info = this.rootRef.el.querySelector("#stock_move_table");
        if (move_info.style.display === "none") {
            move_info.style.display = 'block';
        } else {
            move_info.style.display = 'none';
        }
    }
    // Operation types table details button click
    onclick_operation_type_info() {
        var operation_type_table = this.rootRef.el.querySelector("#operation_type_table");
        if (operation_type_table.style.display === "none") {
            operation_type_table.style.display = 'block';
          } else {
            operation_type_table.style.display = 'none';
        }
    }
    // Product category graph details button click
    onclick_product_category_info() {
        var category = this.rootRef.el.querySelector("#category_table");
        if (category.style.display === "none") {
            category.style.display = 'block';
        } else {
            category.style.display = 'none';
        }
    }
    // Product move info button
    onclick_product_move_info() {
        var category = this.rootRef.el.querySelector("#product_move_table");
        if (category.style.display === "none") {
            category.style.display = 'block';
        } else {
            category.style.display = 'none';
        }
    }
    // Out of stock table details button
    onclick_out_of_stock_info() {
        var out_of_stock_table = this.rootRef.el.querySelector("#out_of_stock_table");
        if (out_of_stock_table.style.display === "none") {
            out_of_stock_table.style.display = 'block';
        } else {
            out_of_stock_table.style.display = 'none';
        }
    }
    // Dead stock table details button
    onclick_dead_stock_info() {
        var dead_stock_table = this.rootRef.el.querySelector("#dead_stock_table");
        if (dead_stock_table.style.display === "none") {
            dead_stock_table.style.display = 'block';
        } else {
            dead_stock_table.style.display = 'none';
        }
    }
    // Top product selection filters
    onchange_top_product_selection(events){
        var option = $(events.target).val();
        // Top product moves in 10 days
        if (option == 'top_last_10_days'){
            this.orm.call("stock.move", "top_products_last_ten", []
            ).then((result) => {
                var ctx = this.rootRef.el.querySelector("#canvaspie");
                var products = result.products
                var count = result.count;
                var countDictionary = {};
                for (var i = 0; i < products.length; i++) {
                    var product = products[i];
                    var productCount = count[i];
                    countDictionary[product] = productCount;
                }
                this.state.countDictionary = countDictionary;
                this.rootRef.el.querySelector("#pro_info").style.display = 'none';
                var myChart = new Chart(ctx, {
                    type: 'bar',
                    data: {
                        labels: products,
                        datasets: [{
                            label: 'Count',
                            data: count,
                            backgroundColor: [
                                "#003f5c","#2f4b7c","#f95d6a","#665191",
                                "#d45087","#ff7c43","#ffa600","#a05195",
                                "#6d5c16","#CCCCFF"
                            ],
                            borderColor: [
                                "#003f5c","#2f4b7c","#f95d6a","#665191",
                                "#d45087","#ff7c43","#ffa600","#a05195",
                                "#6d5c16","#CCCCFF"
                            ],
                            barPercentage: 0.5,
                            barThickness: 6,
                            maxBarThickness: 8,
                            minBarLength: 0,
                            borderWidth: 1,
                            type: 'bar',
                            fill: false
                        }]
                    },
                    options: {
                        scales: {
                            y: {
                                beginAtZero: true
                            },
                        },
                        responsive: true,
                        maintainAspectRatio: false,
                    }
                });
            });
        }
        // Top product moves in 30 days
        if (option == 'top_last_30_days'){
            this.orm.call("stock.move", "top_products_last_thirty", []
            ).then( (result) => {
                var ctx = this.rootRef.el.querySelector("#canvaspie");
                var products = result.products
                var count = result.count;
                var countDictionary = {};
                for (var i = 0; i < products.length; i++) {
                    var product = products[i];
                    var productCount = count[i];
                    countDictionary[product] = productCount;
                }
                this.state.countDictionary = countDictionary;
                this.rootRef.el.querySelector("#pro_info").style.display = 'none';
                var myChart = new Chart(ctx, {
                type: 'bar',
                data: {
                    labels: products,
                     datasets: [{
                        label: 'Count',
                        data: count,
                        backgroundColor: [
                            "#003f5c","#2f4b7c","#f95d6a","#665191",
                            "#d45087","#ff7c43","#ffa600","#a05195",
                            "#6d5c16","#CCCCFF"
                        ],
                        borderColor: [
                            "#003f5c","#2f4b7c","#f95d6a","#665191",
                            "#d45087","#ff7c43","#ffa600","#a05195",
                            "#6d5c16","#CCCCFF"
                        ],
                        barPercentage: 0.5,
                        barThickness: 6,
                        maxBarThickness: 8,
                        minBarLength: 0,
                        borderWidth: 1,
                        type: 'bar',
                        fill: false
                     }]
                },
                options: {
                    scales: {
                        y: {
                            beginAtZero: true
                        },
                    },
                    responsive: true,
                    maintainAspectRatio: false,
                }
                });
            });
        }
        // Top product moves in 3 months
        if (option == 'top_last_3_month'){
            this.orm.call("stock.move", "top_products_last_three_months", []
            ).then( (result) => {
                var ctx = this.rootRef.el.querySelector("#canvaspie");
                var products = result.products
                var count = result.count;
                var countDictionary = {};
                for (var i = 0; i < products.length; i++) {
                    var product = products[i];
                    var productCount = count[i];
                    countDictionary[product] = productCount;
                }
                this.state.countDictionary = countDictionary;
                this.rootRef.el.querySelector("#pro_info").style.display = 'none';
                var myChart = new Chart(ctx, {
                    type: 'bar',
                    data: {
                        labels: products,
                        datasets: [{
                            label: 'Count',
                            data: count,
                            backgroundColor: [
                                "#003f5c","#2f4b7c","#f95d6a","#665191",
                                "#d45087","#ff7c43","#ffa600","#a05195",
                                "#6d5c16","#CCCCFF"
                            ],
                            borderColor: [
                                "#003f5c","#2f4b7c","#f95d6a","#665191",
                                "#d45087","#ff7c43","#ffa600","#a05195",
                                "#6d5c16","#CCCCFF"
                            ],
                            barPercentage: 0.5,
                            barThickness: 6,
                            maxBarThickness: 8,
                            minBarLength: 0,
                            borderWidth: 1,
                            type: 'bar',
                            fill: false
                        }]
                    },
                    options: {
                        scales: {
                            y: {
                                beginAtZero: true
                            },
                        },
                        responsive: true,
                        maintainAspectRatio: false,
                    }
                });
            });
        }
        // Top product moves in last year
        if (option == 'top_last_year'){
            this.orm.call("stock.move", "top_products_last_year",[]
            ).then( (result) => {
                var ctx = this.rootRef.el.querySelector("#canvaspie");
                var products = result.products
                var count = result.count;
                var countDictionary = {};
                for (var i = 0; i < products.length; i++) {
                    var product = products[i];
                    var productCount = count[i];
                    countDictionary[product] = productCount;
                }
                this.state.countDictionary = countDictionary;
                this.rootRef.el.querySelector("#pro_info").style.display = 'none';
                var myChart = new Chart(ctx, {
                    type: 'bar',
                    data: {
                        labels: products,
                        datasets: [{
                            label: 'Count',
                            data: count,
                            backgroundColor: [
                                "#003f5c","#2f4b7c","#f95d6a","#665191",
                                "#d45087","#ff7c43","#ffa600","#a05195",
                                "#6d5c16","#CCCCFF"
                            ],
                            borderColor: [
                                "#003f5c","#2f4b7c","#f95d6a","#665191",
                                "#d45087","#ff7c43","#ffa600","#a05195",
                                "#6d5c16","#CCCCFF"
                            ],
                            barPercentage: 0.5,
                            barThickness: 6,
                            maxBarThickness: 8,
                            minBarLength: 0,
                            borderWidth: 1,
                            type: 'bar',
                            fill: false
                        }]
                    },
                    options: {
                        scales: {
                            y: {
                                beginAtZero: true
                            },
                        },
                        responsive: true,
                        maintainAspectRatio: false,
                    }
                });
            });
        }
    }
    // Stock moves filter
    async onchange_stock_moves_selection(events){
        var option = $(events.target).val();
        // Stock moves in 10 days
        if (option == 'last_10_days'){
            this.orm.call("stock.move", "stock_move_last_ten_days", [option]
            ).then( (result) => {
                var ctx = this.rootRef.el.querySelector("#stock_moves");
                var name = result.name
                var count = result.count;
                var stockMoveDict = {}
                for (var i = 0; i < name.length; i++) {
                    var location = name[i];
                    var stockCount = count[i];
                    stockMoveDict[location] = stockCount;
                }
                this.state.MoveData = stockMoveDict;
                var myChart = new Chart(ctx, {
                    type: 'pie',
                    data: {
                        labels: name,
                        datasets: [{
                            label: 'Count',
                            data: count,
                            backgroundColor: [
                                "#003f5c","#2f4b7c","#f95d6a","#665191",
                                "#d45087","#ff7c43","#ffa600","#a05195",
                                "#6d5c16","#CCCCFF"
                            ],
                            borderColor: [
                                "#003f5c","#2f4b7c","#f95d6a","#665191",
                                "#d45087","#ff7c43","#ffa600","#a05195",
                                "#6d5c16","#CCCCFF"
                            ],
                            barPercentage: 0.5,
                            barThickness: 6,
                            maxBarThickness: 8,
                            minBarLength: 0,
                            borderWidth: 1,
                            type: 'pie',
                            fill: false
                        }]
                    },
                    options: {
                        scales: {
                            y: {
                                beginAtZero: true
                            },
                        },
                        responsive: true,
                        maintainAspectRatio: false,
                    }
                });
            });
        }
        // Stock moves in current month
        if (option == 'this_month'){
            this.orm.call("stock.move", "this_month",[option]
            ).then( (result) => {
                var ctx = this.rootRef.el.querySelector("#stock_moves");
                var name = result.name
                var count = result.count;
                var stockMoveDict = {}
                for (var i = 0; i < name.length; i++) {
                    var location = name[i];
                    var stockCount = count[i];
                    stockMoveDict[location] = stockCount;
                }
                this.state.MoveData = stockMoveDict;
                this.rootRef.el.querySelector("#stock_move_table").style.display = 'none';
                var myChart = new Chart(ctx, {
                    type: 'pie',
                    data: {
                        labels: name,
                        datasets: [{
                            label: 'Count',
                            data: count,
                            backgroundColor: [
                                "#003f5c","#2f4b7c","#f95d6a","#665191",
                                "#d45087","#ff7c43","#ffa600","#a05195",
                                "#6d5c16","#CCCCFF"
                            ],
                            borderColor: [
                                "#003f5c","#2f4b7c","#f95d6a","#665191",
                                "#d45087","#ff7c43","#ffa600","#a05195",
                                "#6d5c16","#CCCCFF"
                            ],
                            barPercentage: 0.5,
                            barThickness: 6,
                            maxBarThickness: 8,
                            minBarLength: 0,
                            borderWidth: 1,
                            type: 'pie',
                            fill: false
                        }]
                    },
                    options: {
                        scales: {
                            y: {
                                beginAtZero: true
                            },
                        },
                        responsive: true,
                        maintainAspectRatio: false,
                    }
                });
            });
        }
        // Stock moves in last 3 months
        if (option == 'last_3_month'){
            this.orm.call("stock.move", "last_three_month", [option]
            ).then( (result) => {
                var ctx = this.rootRef.el.querySelector("#stock_moves");
                var name = result.name
                var count = result.count;
                var stockMoveDict = {}
                for (var i = 0; i < name.length; i++) {
                    var location = name[i];
                    var stockCount = count[i];
                    stockMoveDict[location] = stockCount;
                }
                this.state.MoveData = stockMoveDict;
                this.rootRef.el.querySelector("#stock_move_table").style.display = 'none';
                var myChart = new Chart(ctx, {
                    type: 'pie',
                    data: {
                        labels: name,
                        datasets: [{
                            label: 'Count',
                            data: count,
                            backgroundColor: [
                                "#003f5c","#2f4b7c","#f95d6a","#665191",
                                "#d45087","#ff7c43","#ffa600","#a05195",
                                "#6d5c16","#CCCCFF"
                            ],
                            borderColor: [
                                "#003f5c","#2f4b7c","#f95d6a","#665191",
                                "#d45087","#ff7c43","#ffa600","#a05195",
                                "#6d5c16","#CCCCFF"
                            ],
                            barPercentage: 0.5,
                            barThickness: 6,
                            maxBarThickness: 8,
                            minBarLength: 0,
                            borderWidth: 1,
                            type: 'pie',
                            fill: false
                        }]
                    },
                    options: {
                        scales: {
                            y: {
                                beginAtZero: true
                            },
                        },
                        responsive: true,
                        maintainAspectRatio: false,
                    }
                });
            });
        }
        // Stock moves in last year
        else if (option == 'last_year'){
            this.orm.call("stock.move", "last_year", [option]
            ).then( (result) => {
                var ctx = this.rootRef.el.querySelector("#stock_moves");
                var name = result.name
                var count = result.count;
                this.rootRef.el.querySelector("#stock_move_table").style.display = 'none';
                var stockMoveDict = {}
                for (var i = 0; i < name.length; i++) {
                    var location = name[i];
                    var stockCount = count[i];
                    stockMoveDict[location] = stockCount;
                }
                this.state.MoveData = stockMoveDict;
                    var myChart = new Chart(ctx, {
                    type: 'pie',
                    data: {
                        labels: name,
                        datasets: [{
                            label: 'Count',
                            data: count,
                            backgroundColor: [
                                "#003f5c","#2f4b7c","#f95d6a","#665191",
                                "#d45087","#ff7c43","#ffa600","#a05195",
                                "#6d5c16","#CCCCFF"
                            ],
                            borderColor: [
                                "#003f5c","#2f4b7c","#f95d6a","#665191",
                                "#d45087","#ff7c43","#ffa600","#a05195",
                                "#6d5c16","#CCCCFF"
                            ],
                            barPercentage: 0.5,
                            barThickness: 6,
                            maxBarThickness: 8,
                            minBarLength: 0,
                            borderWidth: 1,
                            type: 'pie',
                            fill: false
                        }]
                    },
                    options: {
                        scales: {
                            y: {
                                beginAtZero: true
                            },
                        },
                        responsive: true,
                        maintainAspectRatio: false,
                    }
                });
            });
        }
    }
    // Product move selection
    onchange_product_moves_selection(events){
        var option = $(events.target).val();
        this.orm.call("stock.move.line", "product_move_by_category", [option]
        ).then( (result) => {
            var ctx = this.rootRef.el.querySelector("#product_move_graph");
            var name = result.name
            var count = result.count;
            this.state.monthly_stock = name
            this.state.monthly_stock_count = count
            this.rootRef.el.querySelector("#product_move_table").style.display = 'none';
            var myChart = new Chart(ctx, {
                type: 'line',
                data: {
                    labels: name,
                    datasets: [{
                        label: 'Quantity Done',
                        data: count,
                        backgroundColor: '#003f5c',
                        borderColor: '#003f5c',
                        barPercentage: 0.5,
                        barThickness: 6,
                        maxBarThickness: 8,
                        minBarLength: 0,
                        borderWidth: 1,
                        type: 'line',
                        fill: false
                    }]
                },
                options: {
                    scales: {
                        y: {
                            beginAtZero: true
                        },
                    },
                    responsive: true,
                    maintainAspectRatio: false,
                }
            });
        });
    }
    // On clicking tiles
    async onclick_tiles (f) {
        var id = parseInt($(f.currentTarget).attr('id'));
        var options = {
            on_reverse_breadcrumb: this.on_reverse_breadcrumb,
        };
        this.env.services['action'].doAction({
            name: _t(op_type[$(f.currentTarget).attr('id')]),
            type: 'ir.actions.act_window',
            res_model: 'stock.picking',
            views: [[false, 'list'], [false, 'form']],
            view_mode: 'tree,form,calendar',
            domain: [['picking_type_id', '=', id]],
            target: 'current',
        }, options);
    }
    // On clicking tile of late status
    onclick_late_status (f) {
        f.stopPropagation();
        var id = parseInt($(f.currentTarget).attr('id'));
        var options = {
            on_reverse_breadcrumb: this.on_reverse_breadcrumb,
        };
        this.env.services['action'].doAction({
            name: _t(op_type[id]+'/Late'),
            type: 'ir.actions.act_window',
            res_model: 'stock.picking',
            view_mode: 'tree,form,calendar',
            views: [[false, 'list'],[false, 'form']],
            domain: [['picking_type_id', '=', id],['state', 'in', ['assigned', 'waiting', 'confirmed']],
                ['scheduled_date', '<=', DateTime.local().toFormat('yyyy-MM-dd')],],
            target: 'current',
        }, options)
    }
    // Onc licking of tile waiting status
    onclick_waiting_status (f) {
        f.stopPropagation();
        var id = parseInt($(f.currentTarget).attr('id'));
        var options = {
            on_reverse_breadcrumb: this.on_reverse_breadcrumb,
        };
        this.env.services['action'].doAction({
            name: _t(op_type[id]+'/Waiting'),
            type: 'ir.actions.act_window',
            res_model: 'stock.picking',
            view_mode: 'tree,form,calendar',
            views: [[false, 'list'],[false, 'form']],
            domain: [['picking_type_id', '=', id],['state', '=', 'confirmed']],
            target: 'current',
        }, options)
    }
    // On clicking of tile backorder status
    onclick_backorders_status (f) {
        f.stopPropagation();
        var id = parseInt($(f.currentTarget).attr('id'));
        var options = {
            on_reverse_breadcrumb: this.on_reverse_breadcrumb,
        };
        this.env.services['action'].doAction({
            name: _t(op_type[id]+'/Backorders'),
            type: 'ir.actions.act_window',
            res_model: 'stock.picking',
            view_mode: 'tree,form,calendar',
            views: [[false, 'list'],[false, 'form']],
            domain: [['picking_type_id', '=', id],['backorder_id', '!=', false]],
            target: 'current',
        }, options)
    }
}
Dashboard.template = "Dashboard";
actionRegistry.add('inventory_dashboard_tag', Dashboard);
