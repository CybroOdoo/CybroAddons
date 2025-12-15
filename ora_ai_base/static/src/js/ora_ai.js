/** @odoo-module **/
import { Component, onMounted, useState } from "@odoo/owl";
import { useBus } from "@web/core/utils/hooks";
import { registry } from "@web/core/registry";
import { VoiceData } from "@ora_ai_base/js/ora_voice_data";

class VoiceAssistant extends Component {
    static components = { VoiceData };
    setup() {
        this.state = useState({
            msg: `Click here to start ${this.props.action.params.assistant_name || 'No Assistant'}`,
            assistant_name: this.props.action.params.assistant_name || 'No Assistant',
        });
        this.vapiReady = false;
        // Store assistant info globally if needed
        window.assistant = this.props.action.params.assistant_id;
        window.apiKey = this.props.action.params.api_key;

        // Dynamically load the VAPI SDK
        onMounted(() => {
            const existingScript = document.querySelector('script[src="/ora_ai_base/static/src/lib/vapi.min.js"]');
            if (!existingScript) {
                const script = document.createElement("script");
                script.src = "/ora_ai_base/static/src/lib/vapi.min.js";
                script.async = true;
                script.defer = true;
                script.onload = () => {
                    this.vapiReady = true;
                                    };
                script.onerror = () => {
                    console.error("Go back to the assistant.");
                };
                document.head.appendChild(script);
            } else {
                this.vapiReady = true; // already loaded
            }
        });
    }
    async start_vapi() {
        const self = this;

        if (!this.vapiReady || !window.vapiSDK || typeof window.vapiSDK.run !== 'function') {
            self.state.msg = "🔄 Voice assistant not ready. Please wait...";
            console.warn("VAPI SDK is not ready yet.");
            return;
        }
        self.state.msg = "🔊 Starting voice assistant...";
        const VAPI = await window.vapiSDK.run({
            apiKey: self.props.action.params.api_key,
            assistant: self.props.action.params.assistant_id,
        });
        if (!VAPI || typeof VAPI.start !== 'function') {
            self.state.msg = "❌ Failed to initialize the assistant.";
            console.error("VAPI object is invalid.");
            return;
        }
        VAPI.start(self.props.action.params.assistant_id);
        VAPI.on("call-end", () => {
            self.state.msg = "✅ Thank you for using the assistant.";
        });
        VAPI.on("message", (message) => {
            if (message.type !== "transcript") return;
            const prefix = message.role === "user" ? "🧑 Me" : "🤖 Assistant";
            if (message.transcriptType === "partial") {
                self.state.msg = `${prefix} (typing...): ${message.transcript}`;
            }
            if (message.transcriptType === "final") {
                self.state.msg = `${prefix}: ${message.transcript}`;
            }
        });
        VAPI.on("error", (e) => {
            console.error("🚨 VAPI Error:", e);
            self.state.msg = "⚠️ Something went wrong. Please try again.";
        });
    }
}
VoiceAssistant.template = 'ora_ai_base.voice_assistant';
registry.category("actions").add("action_voice_assistant", VoiceAssistant);