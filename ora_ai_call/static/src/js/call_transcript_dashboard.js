/** @odoo-module **/
import { registry } from "@web/core/registry";
import { Component } from "@odoo/owl";
import { VoiceData } from "@ora_ai_base/js/ora_voice_data"
//CallTranscript is used to display the transcript of a voice call, particularly for inbound calls.
export class CallTranscript extends Component {
      static components = { VoiceData };
      static template = "call_transcript";
      setup() {
            this.busService = this.env.services.bus_service;
            this.busService.addChannel("inbound_call_channel");
      }
}
registry.category("actions").add("action_call_transcript", CallTranscript);
