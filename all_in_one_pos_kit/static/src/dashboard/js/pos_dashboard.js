/** @odoo-module */
const { Component } = owl;
import { registry } from "@web/core/registry";
import { download } from "@web/core/network/download";
import { useService } from "@web/core/utils/hooks";
import { useRef, useState, onWillStart, onMounted } from "@odoo/owl";
import { BlockUI } from "@web/core/ui/block_ui";
const actionRegistry = registry.category("actions");
import { uiService } from "@web/core/ui/ui_service";
import { renderToElement } from "@web/core/utils/render";

//  Extending components for adding purchase report class
class PosDashboard extends Component {
    async setup() {
    super.setup(...arguments);
    this.orm = useService('orm');
    this.user = useService('user');
    this.canvas_1 = useRef('canvas_1');
    this.pos_sales = useRef('pos_sales');
    this.top_customer = useRef('top_customer');
    this.top_product_categories = useRef('top_product_categories');
    this.top_selling_product = useRef('top_selling_product');
    this.action = useService('action');
    this.state = useState({
            data: null,
            payment_details : [],
            top_salesperson : [],
            selling_product : [],
            total_sale : [],
            total_order_count : [],
            total_refund_count : [],
            total_session : [],
            today_refund_total : [],
            today_sale : [],
    });
    onWillStart(this.fetch_data)
    onMounted(this.render_graphs)
    }
    async fetch_data() {
     //fetch data and call rpc query to create tile.
            self = this;
            let data = await this.orm.call("pos.order", "get_refund_details", [])
            this.state.total_sale = data['total_sale'],
            this.state.total_order_count = data['total_order_count']
            this.state.total_refund_count = data['total_refund_count']
            this.state.total_session = data['total_session']
            this.state.today_refund_total = data['today_refund_total']
            this.state.today_sale = data['today_sale']

            let data2 = await this.orm.call("pos.order", "get_details", [])
            this.state.payment_details = data2['payment_details'];
            this.state.top_salesperson = data2['salesperson'];
            this.state.selling_product = data2['selling_product'];

        }
        async pos_order_today(e) {
        //Click function returns today's all pos order tree view.
            let date = new Date();
            let yesterday = new Date(date.getTime());
            yesterday.setDate(date.getDate() - 1);
            e.stopPropagation();
            e.preventDefault();
            let has_group = await this.user.hasGroup("hr.group_hr_user")
                if (has_group) {
                    this.action.doAction({
                        name: "Today Order",
                        type: 'ir.actions.act_window',
                        res_model: 'pos.order',
                        view_mode: 'tree,form,calendar',
                        view_type: 'form',
                        views: [
                            [false, 'list'],
                            [false, 'form']
                        ],
                        domain: [
                            ['date_order', '<=', date],
                            ['date_order', '>=', yesterday]
                        ],
                        target: 'current'
                    }, {
                        on_reverse_breadcrumb: this.on_reverse_breadcrumb
                    })
                }
        }
        async pos_refund_orders(e) {
         //Click function returns all refund pos order tree view.
            e.stopPropagation();
            e.preventDefault();
            let has_group = await this.user.hasGroup('hr.group_hr_user')
                if (has_group) {
                    this.action.doAction({
                        name: "Refund Orders",
                        type: 'ir.actions.act_window',
                        res_model: 'pos.order',
                        view_mode: 'tree,form,calendar',
                        view_type: 'form',
                        views: [
                            [false, 'list'],
                            [false, 'form']
                        ],
                        domain: [
                            ['amount_total', '<', 0.0]
                        ],
                        target: 'current'
                    }, {
                        on_reverse_breadcrumb: this.on_reverse_breadcrumb
                    })
                }
        }
        async pos_refund_today_orders(e) {
        //Click function returns all today's refund pos order in tree view.
            let date = new Date();
            let yesterday = new Date(date.getTime());
            yesterday.setDate(date.getDate() - 1);
            e.stopPropagation();
            e.preventDefault();
            let has_group = await this.user.hasGroup('hr.group_hr_user')
                if (has_group) {
                    this.action.doAction({
                        name: "Refund Orders",
                        type: 'ir.actions.act_window',
                        res_model: 'pos.order',
                        view_mode: 'tree,form,calendar',
                        view_type: 'form',
                        views: [
                            [false, 'list'],
                            [false, 'form']
                        ],
                        domain: [
                            ['amount_total', '<', 0.0],
                            ['date_order', '<=', date],
                            ['date_order', '>=', yesterday]
                        ],
                        target: 'current'
                    }, {
                        on_reverse_breadcrumb: this.on_reverse_breadcrumb
                    })
                }
        }
        async pos_order(e) {
         //Click function returns all pos order in tree view.
            e.stopPropagation();
            e.preventDefault();
            let has_group = await this.user.hasGroup('hr.group_hr_user')
                if (has_group) {
                    this.action.doAction({
                        name: "Total Order",
                        type: 'ir.actions.act_window',
                        res_model: 'pos.order',
                        view_mode: 'tree,form,calendar',
                        view_type: 'form',
                        views: [
                            [false, 'list'],
                            [false, 'form']
                        ],
                        target: 'current'
                    }, {
                        on_reverse_breadcrumb: this.on_reverse_breadcrumb
                    })
                }
        }
        async pos_session(e) {
        //Click function returns all pos session in tree view.
            e.stopPropagation();
            e.preventDefault();
            let has_group = await this.user.hasGroup('hr.group_hr_user')
                if (has_group) {
                    this.action.doAction({
                        name: "sessions",
                        type: 'ir.actions.act_window',
                        res_model: 'pos.session',
                        view_mode: 'tree,form,calendar',
                        view_type: 'form',
                        views: [
                            [false, 'list'],
                            [false, 'form']
                        ],
                        target: 'current'
                    }, {
                        on_reverse_breadcrumb: this.on_reverse_breadcrumb
                    })
                }
        }
        async onclick_pos_sales(events) {
        // Function to add filter in pos sales report
            let ctx = this.canvas_1.el;
            console.log('ctx',ctx)
            let arrays = await this.orm.call("pos.order","get_department", [this.pos_sales.el.value])
            console.log('arrays',arrays)
                if (window.myCharts != undefined)
                    window.myCharts.destroy();
                window.myCharts = new Chart(ctx, {
                    type: "bar",
                    data: {
                        labels: arrays[1],
                        datasets: [{
                            label: arrays[2],
                            data: arrays[0],
                            backgroundColor: [
                                "rgba(255, 99, 132,1)",
                                "rgba(54, 162, 235,1)",
                                "rgba(75, 192, 192,1)",
                                "rgba(153, 102, 255,1)",
                                "rgba(10,20,30,1)"
                            ],
                            borderColor: [
                                "rgba(255, 99, 132, 0.2)",
                                "rgba(54, 162, 235, 0.2)",
                                "rgba(75, 192, 192, 0.2)",
                                "rgba(153, 102, 255, 0.2)",
                                "rgba(10,20,30,0.3)"
                            ],
                            borderWidth: 1
                        }, ]
                    },
                    options: {
                        responsive: true,
                        title: {
                            display: true,
                            position: "top",
                            text: "SALE DETAILS",
                            fontSize: 18,
                            fontColor: "#111"
                        },
                        legend: {
                            display: true,
                            position: "bottom",
                            labels: {
                                fontColor: "#333",
                                fontSize: 16
                            }
                        },
                        scales: {
                            yAxes: [{
                                ticks: {
                                    min: 0
                                }
                            }]
                        }
                    }
                });
        }

     async render_graphs() {
           //Add function to load in dashboard.
           await this.render_top_customer_graph();
           await this.render_top_product_graph();
           await this.render_product_category_graph();
        }
     async render_top_customer_graph() {
            //Function to create top customers chart
            let ctx = this.top_customer.el;
            console.log('ctxctx',ctx)
            let arrays = await this.orm.call('pos.order','get_the_top_customer',[])
            console.log('arraysarrays',arrays)
            console.log('arrays[1]',arrays[1])
            console.log('arrays[0]',arrays[0])
            let chart = new Chart(ctx, {
                 //create Chart class object
                    type: "pie",
                    data: {
                        labels: arrays[1],
                        datasets: [{
                                label: "",
                                data: arrays[0],
                                backgroundColor: [
                                    "rgb(148, 22, 227)",
                                    "rgba(54, 162, 235)",
                                    "rgba(75, 192, 192)",
                                    "rgba(153, 102, 255)",
                                    "rgba(10,20,30)"
                                ],
                                borderColor: [
                                    "rgba(255, 99, 132,)",
                                    "rgba(54, 162, 235,)",
                                    "rgba(75, 192, 192,)",
                                    "rgba(153, 102, 255,)",
                                    "rgba(10,20,30,)"
                                ],
                                borderWidth: 1
                            },
                        ]
                    },
                    options: { //options
                        responsive: true,
                        title: {
                            display: true,
                            position: "top",
                            text: " Top Customer",
                            fontSize: 18,
                            fontColor: "#111"
                        },
                        legend: {
                            display: true,
                            position: "bottom",
                            labels: {
                                fontColor: "#333",
                                fontSize: 16
                            }
                        },
                        scales: {
                            yAxes: [{
                                ticks: {
                                    min: 0
                                }
                            }]
                        }
                    }
                });
        }
     async render_top_product_graph() {
         //Function to create top product chart.
            let ctx = this.top_selling_product.el;
            let arrays = await this.orm.call('pos.order','get_the_top_products',[])
            let chart = new Chart(ctx, { //create Chart class object
                type: "horizontalBar",
                data: {
                    labels: arrays[1],
                    datasets: [{
                        label: "Quantity",
                        data: arrays[0],
                        backgroundColor: [
                            "rgba(255, 99, 132,1)",
                            "rgba(54, 162, 235,1)",
                            "rgba(75, 192, 192,1)",
                            "rgba(153, 102, 255,1)",
                            "rgba(10,20,30,1)"
                        ],
                        borderColor: [
                            "rgba(255, 99, 132, 0.2)",
                            "rgba(54, 162, 235, 0.2)",
                            "rgba(75, 192, 192, 0.2)",
                            "rgba(153, 102, 255, 0.2)",
                            "rgba(10,20,30,0.3)"
                        ],
                        borderWidth: 1
                    }, ]
                },
                options: { //options
                    responsive: true,
                    title: {
                        display: true,
                        position: "top",
                        text: " Top products",
                        fontSize: 18,
                        fontColor: "#111"
                    },
                    legend: {
                        display: true,
                        position: "bottom",
                        labels: {
                            fontColor: "#333",
                            fontSize: 16
                        }
                    },
                    scales: {
                        yAxes: [{
                            ticks: {
                                min: 0
                            }
                        }]
                    }
                }
            });
        }
     async render_product_category_graph() {
     //Function to create top categories chart
            var ctx = this.top_product_categories.el;
            let arrays = await this.orm.call('pos.order','get_the_top_categories',[])
            let chart = new Chart(ctx, {
            //create Chart class object
                    type: "horizontalBar",
                    data: {
                        labels: arrays[1],
                        datasets: [{
                            label: "Quantity",
                            data: arrays[0],
                            backgroundColor: [
                                "rgba(255, 99, 132,1)",
                                "rgba(54, 162, 235,1)",
                                "rgba(75, 192, 192,1)",
                                "rgba(153, 102, 255,1)",
                                "rgba(10,20,30,1)"
                            ],
                            borderColor: [
                                "rgba(255, 99, 132, 0.2)",
                                "rgba(54, 162, 235, 0.2)",
                                "rgba(75, 192, 192, 0.2)",
                                "rgba(153, 102, 255, 0.2)",
                                "rgba(10,20,30,0.3)"
                            ],
                            borderWidth: 1
                        }, ]
                    },
                    options: {
                        responsive: true,
                        title: {
                            display: true,
                            position: "top",
                            text: " Top product categories",
                            fontSize: 18,
                            fontColor: "#111"
                        },
                        legend: {
                            display: true,
                            position: "bottom",
                            labels: {
                                fontColor: "#333",
                                fontSize: 16
                            }
                        },
                        scales: {
                            yAxes: [{
                                ticks: {
                                    min: 0
                                }
                            }]
                        }
                    }
                });
        }
 }
 PosDashboard.template = "PosDashboard";
actionRegistry.add("pos_dashboard", PosDashboard);