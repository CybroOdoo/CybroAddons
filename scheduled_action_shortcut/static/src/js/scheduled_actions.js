 /** @odoo-module **/
 import { useService } from "@web/core/utils/hooks";

 const { Component, xml, onMounted, useRef, useEffect, onWillDestroy } = owl;
/**
 * ScheduledActionsTemplate component for displaying scheduled actions in the systray.
 */
 export class ScheduledActionsTemplate extends owl.Component {
     setup() {
         super.setup()
         this.orm = useService("orm");
         this.env.bus.addEventListener("closeAllEvent:SA", () => document.body.removeEventListener("click",this.closeDropdown.bind(this)))
         this.root = useRef("botIcon")
         onMounted(this.scheduled_action_records)
         useEffect(() => {  ``
            document.body.addEventListener("click",this.closeDropdown.bind(this))
            return () => {
                document.body.removeEventListener("click",this.closeDropdown.bind(this))
            }
         }, () => [])
         onWillDestroy(() => document.body.removeEventListener("click",this.closeDropdown.bind(this)))
     }
     //    This is a on mound function and it will return the ir.cron data based on the domain and it will append to the template.
     async scheduled_action_records() {
         var self = this;
        await this.orm.call("ir.cron", "search_read", [], {
             domain: [['run_through_systray', '=', 'True']],
         }).then(function(data) {
             var div_body = $(self.__owl__.bdom.el).find('.cron_msg')
             if (data.length == 0) {
                 div_body.append("<p class='cron_empty_container'>There is no scheduled actions here, Enable the boolean to run.</p>")
             } else if (data.length > 0) {
                 data.forEach(function(res) {
                     div_body.append("<div class='cron_container'><div><p class='cron_name p_class'>" + res.cron_name + "</p><p class='cron_nextcall p_class'>Next Call : " + res.nextcall + "</p></div><button id=" + res.id + " class='cron_btn btn-primary'>Run</button></div>")
                 });
             }
         })
         // This is for Call the button to Run
         $(self.__owl__.bdom.el).find('.cron_btn').click(function(ev) {
             self.cron_run_button(ev)
         });
     }
     // Passing the corresponding cron data through rpc
     cron_run_button(ev) {
         var cron_id = parseInt(ev.currentTarget.id)
         this.orm.call('ir.cron', 'run_scheduled_actions', [cron_id]);
     }
     closeDropdown(ev) {
         if (this.root.el && !this.root.el?.contains(ev.target)) {
            document.body.removeEventListener("click",this.closeDropdown.bind(this))
            this.props.setDropDown(false)
            this.root.el.remove()
            return
         }
         document.body.removeEventListener("click",this.closeDropdown.bind(this))
     }
 }
 // Template for scheduled action on the systray
 ScheduledActionsTemplate.template = xml`
                                        <div class="botIcon" t-ref="botIcon">
                                                <div class="s_action_name cron_msg">
                                                </div>
                                        </div>`
