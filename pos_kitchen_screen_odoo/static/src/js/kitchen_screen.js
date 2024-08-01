/** @odoo-module */

import { registry } from "@web/core/registry";
const { Component, onWillStart, useState, onMounted } = owl;
import { useService } from "@web/core/utils/hooks";


class kitchen_screen_dashboard extends Component {

    setup() {
        super.setup();
        this.busService = this.env.services.bus_service;
        this.busService.addChannel("pos_order_created");
        onWillStart(() => {
        this.busService.addEventListener('notification', this.onPosOrderCreation.bind(this));})
        this.action = useService("action");
        this.rpc = this.env.services.rpc;
        this.action = useService("action");
        this.orm = useService("orm");
        var self=this
        this.state = useState({
            order_details: [],
            shop_id:[],
            stages: 'draft',
            draft_count:[],
            waiting_count:[],
            ready_count:[],
            lines:[]
        });
        var session_shop_id;
        //if refreshing the page then the last passed context (shop id)
        //save to the session storage
        if (this.props.action.context.default_shop_id) {
            sessionStorage.setItem('shop_id', this.props.action.context.default_shop_id);
            this.shop_id = this.props.action.context.default_shop_id;
            session_shop_id = sessionStorage.getItem('shop_id');
        } else {
            session_shop_id = sessionStorage.getItem('shop_id');
            this.shop_id = parseInt(session_shop_id, 10);;
        }
        self.orm.call("pos.order", "get_details", ["", self.shop_id,""]).then(function(result) {
            self.state.order_details = result['orders']
            self.state.lines = result['order_lines']
            self.state.shop_id=self.shop_id
            self.state.draft_count=self.state.order_details.filter((order) => order.order_status=='draft' && order.config_id[0]==self.state.shop_id).length
            self.state.waiting_count=self.state.order_details.filter((order) => order.order_status=='waiting' && order.config_id[0]==self.state.shop_id).length
            self.state.ready_count=self.state.order_details.filter((order) => order.order_status=='ready' && order.config_id[0]==self.state.shop_id).length
        });
    }

    //Calling the onPosOrderCreation when an order is created or edited on the backend and return the notification
    onPosOrderCreation(message){
        let payload = message.detail[0].payload
        var self=this
        if(payload.message == "pos_order_created" && payload.res_model == "pos.order"){
            self.orm.call("pos.order", "get_details", ["", self.shop_id,""]).then(function(result) {
            self.state.order_details = result['orders']
            self.state.lines = result['order_lines']
            self.state.shop_id=self.shop_id
            self.state.draft_count=self.state.order_details.filter((order) => order.order_status=='draft' && order.config_id[0]==self.state.shop_id).length
            self.state.waiting_count=self.state.order_details.filter((order) => order.order_status=='waiting' && order.config_id[0]==self.state.shop_id).length
            self.state.ready_count=self.state.order_details.filter((order) => order.order_status=='ready' && order.config_id[0]==self.state.shop_id).length
            });
        }
    }

    // cancel the order from the kitchen
    cancel_order(e) {
         var input_id = $("#" + e.target.id).val();
         this.orm.call("pos.order", "order_progress_cancel", [Number(input_id)])
         var current_order = this.state.order_details.filter((order) => order.id==input_id)
         if(current_order){
            current_order[0].order_status = 'cancel'
         }
    }
    // accept the order from the kitchen
        accept_order(e) {
        var input_id = $("#" + e.target.id).val();
        ScrollReveal().reveal("#" + e.target.id, {
            delay: 1000,
            duration: 2000,
            opacity: 0,
            distance: "50%",
            origin: "top",
            reset: true,
            interval: 600,
        });
         var self=this
         this.orm.call("pos.order", "order_progress_draft", [Number(input_id)])
         var current_order = this.state.order_details.filter((order) => order.id==input_id)
         if(current_order){
            current_order[0].order_status = 'waiting'
         }
    }
    // set the stage is ready to see the completed stage orders
    ready_stage(e) {
        var self = this;
        self.state.stages = 'ready';
    }
    //set the stage is waiting to see the ready stage orders
    waiting_stage(e) {
        var self = this;
        self.state.stages = 'waiting';
    }
    //set the stage is draft to see the cooking stage orders
    draft_stage(e) {
        var self = this;
        self.state.stages = 'draft';
    }
    // change the status of the order from the kitchen
    done_order(e) {
        var self = this;
        var input_id = $("#" + e.target.id).val();
        this.orm.call("pos.order", "order_progress_change", [Number(input_id)])
        var current_order = this.state.order_details.filter((order) => order.id==input_id)
         if(current_order){
            current_order[0].order_status = 'ready'
         }
    }
    // change the status of the product from the kitchen
    accept_order_line(e) {
        var input_id = $("#" + e.target.id).val();
        this.orm.call("pos.order.line", "order_progress_change", [Number(input_id)])
        var current_order_line=this.state.lines.filter((order_line) => order_line.id==input_id)
        if (current_order_line){
            if (current_order_line[0].order_status == 'ready'){
                current_order_line[0].order_status = 'waiting'
            }
            else{
                current_order_line[0].order_status = 'ready'
            }
        }
    }

}
kitchen_screen_dashboard.template = 'KitchenCustomDashBoard';
registry.category("actions").add("kitchen_custom_dashboard_tags", kitchen_screen_dashboard);