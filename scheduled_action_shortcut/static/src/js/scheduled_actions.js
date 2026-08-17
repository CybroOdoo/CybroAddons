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
             var div_body = self.root.el.lastChild
             if (data.length == 0) {
                let emptyMessage = document.createElement('p');
                emptyMessage.className = 'cron_empty_container';
                emptyMessage.textContent = "There is no scheduled actions here. Enable the boolean to run.";
                div_body.appendChild(emptyMessage);
            } else if (data.length > 0) {
                data.forEach(function(res) {
                    let cronContainer = document.createElement('div');
                    cronContainer.className = 'cron_container';
                    let cronInfo = document.createElement('div');
                    let cronName = document.createElement('p');
                    cronName.className = 'cron_name p_class';
                    cronName.textContent = res.cron_name;
                    let cronNextCall = document.createElement('p');
                    cronNextCall.className = 'cron_nextcall p_class';
                    cronNextCall.textContent = "Next Call: " + res.nextcall;
                    cronInfo.appendChild(cronName);
                    cronInfo.appendChild(cronNextCall);
                    let runButton = document.createElement('button');
                    runButton.id = res.id;
                    runButton.className = 'cron_btn btn-primary';
                    runButton.textContent = "Run";
                    runButton.addEventListener('click', function(ev) {
                        self.cron_run_button(ev);
                    });
                    cronContainer.appendChild(cronInfo);
                    cronContainer.appendChild(runButton);
                    div_body.appendChild(cronContainer);
                });
            }
        })
    }
     // Passing the corresponding cron data through rpc
     cron_run_button(ev) {
         var cron_id = parseInt(ev.target.id)
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