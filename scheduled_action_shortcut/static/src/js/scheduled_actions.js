 /** @odoo-module **/
 import rpc from 'web.rpc';
 const { Component } = owl;
 import { useEffect } from '@web/core/utils/hooks';
 const { useRef, onMounted } = owl.hooks;
 const { xml } = owl.tags;
/**
 * ScheduledActionsTemplate component for displaying scheduled actions in the systray.
 */
 export class ScheduledActionsTemplate extends owl.Component {
     setup() {
         super.setup()
         this.env.bus.on("closeAllEvent:SA", this, this.closeDropdown.bind(this))
         this.root = useRef("botIcon")
         onMounted(this.scheduled_action_records)
         useEffect(() => {
            document.body.addEventListener("click",this.closeDropdown.bind(this))
            return () => {
                document.body.removeEventListener("click",this.closeDropdown.bind(this))
            }
         }, () => [])
     }
     //    This is a on mound function and it will return the ir.cron data based on the domain and it will append to the template.
     async scheduled_action_records() {
         var self = this
         await rpc.query({
             model: 'ir.cron',
             method: 'search_read',
             domain: [
                 ['run_through_systray', '=', 'True']
             ],
             args: [],
         }).then(function(data) {
             var div_body = $(self.__owl__.vnode.children[0].elm)
             if (data.length == 0) {
                 div_body.append("<p class='cron_empty_container'>There is no scheduled actions here, Enable the boolean to run.</p>")
             } else if (data.length > 0) {
                 data.forEach(function(res) {
                     var scheduled_action_date = moment.utc(res.nextcall).local();
                     var formatted_date = scheduled_action_date.format('DD-MM-YYYY HH:mm:ss');
                     div_body.append("<div class='cron_container'><div><p class='cron_name p_class'>" + res.cron_name + "</p><p class='cron_nextcall p_class'>Next Call : " + formatted_date + "</p></div><button id=" + res.id + " class='cron_btn btn-primary'>Run</button></div>")
                 });
             }
         })
         //This is for Call the button to Run
         $(self.__owl__.vnode.children[0].elm).find('.cron_btn').click(function(ev) {
             self.cron_run_button(ev)
         });
     }
     //    Passing the corresponding cron data through rpc
     cron_run_button(ev) {
         var cron_id = parseInt(ev.currentTarget.id)
         rpc.query({
             'model': 'ir.cron',
             'method': 'run_scheduled_actions',
             'args': [
                 [cron_id]
             ],
         });
     }
     closeDropdown(ev) {
         if (this.root.el) {
            document.body.removeEventListener("click",this.closeDropdown.bind(this))
            this.props.setDropDown = false
            this.root.el.remove()
            return
         }
         document.body.removeEventListener("click",this.closeDropdown.bind(this))
     }
 }
 //    Template for scheduled action on the systray
 ScheduledActionsTemplate.template = xml`
                                        <div class="botIcon" t-ref="botIcon">
                                                <div class="s_action_name cron_msg">
                                                </div>
                                        </div>`
