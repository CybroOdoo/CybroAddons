/** @odoo-module **/
import { registry } from "@web/core/registry";
import { session } from "@web/session";
import { _t } from "@web/core/l10n/translation";
import { Component } from "@odoo/owl";
import { onWillStart, onMounted, useState } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";
import { user } from "@web/core/user";
const actionRegistry = registry.category("actions");
export class PosDashboard extends Component{
//Initializes the PosDashboard component,
    setup() {
            super.setup(...arguments);
            this.orm = useService('orm')
            this.user = user;
            this.actionService = useService("action");
            this.state = useState({
                payment_details : [],
                top_salesperson : [],
                selling_product : [],
                total_sale: [],
                total_order_count: [],
                total_refund_count : [],
                total_session:[],
                today_refund_total:[],
                today_sale:[],
            });
            // When the component is about to start, fetch data in tiles
            onWillStart(async () => {
                await this.fetch_data();
            });
            //When the component is mounted, render various charts
            onMounted(async () => {
                await this.render_top_customer_graph();
                await this.render_top_product_graph();
                await this.render_product_category_graph();
                await this.onclick_pos_sales('Hourly');
            });
    }
    async fetch_data() {
    //  Function to fetch all the pos details
        var result = await this.orm.call('pos.order','get_refund_details',[])
             this.state.total_sale = result['total_sale'],
             this.state.total_order_count = result['total_order_count']
             this.state.total_refund_count = result['total_refund_count']
             this.state.total_session = result['total_session']
             this.state.today_refund_total = result['today_refund_total']
             this.state.today_sale = result['today_sale']
        var data =  await this.orm.call('pos.order','get_details',[])
             this.state.payment_details = data['payment_details']
             this.state.top_salesperson = data['salesperson']
             this.state.selling_product = data['selling_product']
    }
    pos_order_today (e){
    //To get the details of today's order
        var self = this;
        var date = new Date();
        var yesterday = new Date(date.getTime());
        yesterday.setDate(date.getDate() - 1);
        e.stopPropagation();
        e.preventDefault();
        this.user.hasGroup('hr.group_hr_user').then(function(has_group){
            if(has_group){
                var options = {
                    on_reverse_breadcrumb: self.on_reverse_breadcrumb,
                };
                 self.actionService.doAction({
                    name: _t("Today Order"),
                    type: 'ir.actions.act_window',
                    res_model: 'pos.order',
                    view_mode: 'tree,form,calendar',
                    view_type: 'form',
                    views: [[false, 'list'],[false, 'form']],
                    domain: [['date_order','<=', date],['date_order', '>=', yesterday]],
                    target: 'current'
                }, options)
            }
        });
    }
    pos_refund_orders (e){
    //   To get the details of refund orders
        var self = this;
        var date = new Date();
        var yesterday = new Date(date.getTime());
        yesterday.setDate(date.getDate() - 1);
        e.stopPropagation();
        e.preventDefault();
        this.user.hasGroup('hr.group_hr_user').then(function(has_group){
            if(has_group){
                var options = {
                    on_reverse_breadcrumb: self.on_reverse_breadcrumb,
                };
                self.actionService.doAction({
                    name: _t("Refund Orders"),
                    type: 'ir.actions.act_window',
                    res_model: 'pos.order',
                    view_mode: 'tree,form,calendar',
                    view_type: 'form',
                    views: [[false, 'list'],[false, 'form']],
                    domain: [['amount_total', '<', 0.0]],
                    target: 'current'
                }, options)
            }
        });
    }
    pos_refund_today_orders (e){
    //  To get the details of today's order
        var self = this;
        var date = new Date();
        var yesterday = new Date(date.getTime());
        yesterday.setDate(date.getDate() - 1);
        e.stopPropagation();
        e.preventDefault();
        this.user.hasGroup('hr.group_hr_user').then(function(has_group){
            if(has_group){
                var options = {
                    on_reverse_breadcrumb: self.on_reverse_breadcrumb,
                };
                self.actionService.doAction({
                    name: _t("Refund Orders"),
                    type: 'ir.actions.act_window',
                    res_model: 'pos.order',
                    view_mode: 'tree,form,calendar',
                    view_type: 'form',
                    views: [[false, 'list'],[false, 'form']],
                    domain: [['amount_total', '<', 0.0],['date_order','<=', date],['date_order', '>=', yesterday]],
                    target: 'current'
                }, options)
            }
        });
    }
     pos_order (e){
    //    To get total orders details
        var self = this;
        var date = new Date();
        var yesterday = new Date(date.getTime());
        yesterday.setDate(date.getDate() - 1);
        e.stopPropagation();
        e.preventDefault();
        this.user.hasGroup('hr.group_hr_user').then(function(has_group){
            if(has_group){
                var options = {
                    on_reverse_breadcrumb: self.on_reverse_breadcrumb,
                };
                self.actionService.doAction({
                    name: _t("Total Order"),
                    type: 'ir.actions.act_window',
                    res_model: 'pos.order',
                    view_mode: 'tree,form,calendar',
                    view_type: 'form',
                    views: [[false, 'list'],[false, 'form']],
                    target: 'current'
                }, options)
            }
        });
    }
    pos_session (e){
    //    To get the Session wise details
        var self = this;
        e.stopPropagation();
        e.preventDefault();
         this.user.hasGroup('hr.group_hr_user').then(function(has_group){
            if(has_group){
                var options = {
                    on_reverse_breadcrumb: self.on_reverse_breadcrumb,
                };
                self.actionService.doAction({
                    name: _t("sessions"),
                    type: 'ir.actions.act_window',
                    res_model: 'pos.session',
                    view_mode: 'tree,form,calendar',
                    view_type: 'form',
                    views: [[false, 'list'],[false, 'form']],
                    target: 'current'
                }, options)
            }
        });
    }
    onclick_pos_sales (events){
    //  To get the Sale bar chart
       var option = $(events.target).val();
       var self = this
        var ctx = $("#canvas_1");
        this.orm.call('pos.order', 'get_department',[option])
            .then(function (arrays) {
          var data = {
            labels: arrays[1],
            datasets: [
              {
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
              },
            ]
          };
    //options
          var options = {
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
            }
          };
          //create Chart class object
          if (window.myCharts != undefined)
          window.myCharts.destroy();
          window.myCharts = new Chart(ctx, {
            type: "bar",
            data: data,
            options: options
          });

        });
        }
    render_top_customer_graph(){
    //      To render the top customer pie chart
       var self = this
       var ctx = $(".top_customer");
       this.orm.call('pos.order', 'get_the_top_customer')
        .then(function (arrays) {
          var data = {
            labels: arrays[1],
            datasets: [
              {
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
          };
    //options
          var options = {
            responsive: true,
             scales: {
          x: {
            title: {
              display: true,
              text: "Top Customer",
              position: "top",
              fontSize: 24,
              color: "#111"
            }
          }
        },
            legend: {
              display: true,
              position: "bottom",
              labels: {
                fontColor: "#333",
                fontSize: 16
              }
            }
          };
          //create Chart class object
          var chart = new Chart(ctx, {
            type: "pie",
            data: data,
            options: options
          });

        });
        }
    render_top_product_graph (){
     //   To render the top product graph
       var self = this
        var ctx = $(".top_selling_product");
       this.orm.call('pos.order', 'get_the_top_products')
            .then(function (arrays) {
          var data = {

            labels: arrays[1],
            datasets: [
              {
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
              },

            ]
          };
    //options
          var options = {
            responsive: true,
            indexAxis: 'y',
            legend: {
              display: true,
              position: "bottom",
              labels: {
                fontColor: "#333",
                fontSize: 16
              }
            },
             scales: {
          x: {
            title: {
              display: true,
              text: "Top products",
              position: "top",
              fontSize: 24,
              color: "#111"
            }
          }
        },
          };
          //create Chart class object
          var chart = new Chart(ctx, {
            type: "bar",
            data: data,
            options: options
          });
        });
        }
    render_product_category_graph (){
        //    To render the product category graph
           var self = this
        var ctx = $(".top_product_categories");
        this.orm.call('pos.order', 'get_the_top_categories')
            .then(function (arrays) {
          var data = {
            labels: arrays[1],
            datasets: [
              {
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
              },
            ]
          };
    //options
          var options = {
            responsive: true,
             scales: {
          x: {
            title: {
              display: true,
              text: "Top product categories",
              position: "top",
              fontSize: 24,
              color: "#111"
            }
          }
        },
            legend: {
              display: true,
              position: "bottom",
              labels: {
                fontColor: "#333",
                fontSize: 16
              }
            },
            indexAxis: 'y',
          };
          //create Chart class object
          var chart = new Chart(ctx, {
            type: "bar",
            data: data,
            options: options
          });
        });
        }
}
PosDashboard.template = 'PosDashboard'
registry.category("actions").add("pos_order_menu", PosDashboard)
