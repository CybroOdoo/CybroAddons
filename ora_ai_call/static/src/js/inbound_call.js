/** @odoo-module **/
import { Component, useState } from "@odoo/owl";
import { registry } from "@web/core/registry";
let hours = 0;
let minutes = 0;
let seconds = 0;
var timerInterval;
//Manages the UI and call duration tracking for an ongoing outbound voice call.
class VapiCalling extends Component {
    setup(){
        this.state = useState({duration:"......"})
        this.busService = this.env.services.bus_service
        this.channel = "vapi_call_channel"
        this.busService.addChannel(this.channel)
        this.busService.subscribe("notification", this.onMessage.bind(this))
    }
    onMessage(notifications) {
      if(notifications){
        if (notifications.value.message.status === "in-progress"){
            timerInterval = setInterval(this.updateTimer.bind(this), 1000);
        }
        if (notifications.value.message.status === "ended"){
            clearInterval(timerInterval)
        }
      }
    }
    updateTimer() {
         seconds++;
            // If seconds reach 60, reset them to 0 and increment minutes
         if (seconds === 60) {
                seconds = 0;
                minutes++;
            }
            // If minutes reach 60, reset them to 0 and increment hours
            if (minutes === 60) {
                minutes = 0;
                hours++;
            }
            // Display the updated time
           this.state.duration = hours +":"+ minutes +":"+seconds;
        }
}
VapiCalling.template = 'ora_ai_base.phone_call';
registry.category("actions").add("action_vapi_outbound_calling", VapiCalling);
