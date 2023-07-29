/** @odoo-module **/
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { session } from '@web/session';
const { mount, useState, onMounted, useEffect } = owl;
var rpc = require('web.rpc')

class ScheduledActions extends owl.Component {
    setup() {
        this.action = useService("action");
        this.state = useState({
            task_details : [],
            purchase_details : [],
            sale_details : [],
            crm_details : [],
        })
        onMounted(
            () => this.__owl__.bdom.el.ownerDocument.addEventListener(
            "click", this.body_click)
            )
        useEffect(() => {
            this.check_grp()
        });
        super.setup()
    }
   // Perform an RPC query to retrieve task details, purchase details, sale details, and CRM details
    _onClick() {
        var self = this;
        rpc.query({
            model: 'project.task',
            method: 'task_assigned',
            args: [],

        }).then(function (res) {
           self.state.task_details = res[0]
           self.state.purchase_details = res[1]
           self.state.sale_details = res[2]
           self.state.crm_details = res[3]

        });
        if (this.__owl__.bdom.el.querySelectorAll("#announcement_div")[0].style.display != "block"){
            this.__owl__.bdom.el.querySelectorAll("#announcement_div")[0].style.display = "block"
        }else if (this.__owl__.bdom.el.querySelectorAll("#announcement_div")[0].style.display == "block"){
            this.__owl__.bdom.el.querySelectorAll("#announcement_div")[0].style.display = "none"
        }
    }
    async check_grp(){
        let self = this
        await rpc.query({
            model: 'res.users',
            method: 'has_group',
            args: ['all_in_one_announcements.announcement_group_manager'],
        }).then(function(res){
            if(!res){
                self.__owl__.bdom.el.querySelectorAll("#dropdownMenuButton1")[0].hidden = true
            }
        })
    }
    // Check if the current user has a specific group and hide an element if not
    body_click(ev){
        if( !ev.target.classList.contains("list_headers")){
            if ($(this.querySelector("#announcement_div"))[0].style.display == "block"){

                $(this.querySelector("#announcement_div"))[0].style.display = "none"
            }
        }
    }
    // Method called when a task view is opened
    openTaskView(ev){
        var self = this;
        var model_id = ev.target.getAttribute('data-model')
        rpc.query({
            model: model_id,
            method:'get_pending_tasks',
            args:[ev.target.getAttribute('data-id')]
        }).then(function(result){
             self.action.doAction(result)
        })
    }
    }
    // Set the template for the ScheduledActions component
    ScheduledActions.template = "all_in_one_announcementsSystray";
   export const systrayItem = {
    Component: ScheduledActions
};
registry.category("systray")
    .add("ScheduledActions", systrayItem, {
        sequence: 1
    });