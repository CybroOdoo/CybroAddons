/** @odoo-module **/
import { Component, onMounted, onWillStart, onWillUnmount, proxy, useProps } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { standardActionServiceProps } from "@web/webclient/actions/action_plugin";
import { useService } from "@web/core/utils/hooks";
import { loadJS } from "@web/core/assets";
import { VoiceData } from "@ora_ai_base/js/ora_voice_data";

// Prevent Krisp / WebRTC noise-cancellation module loading errors from interrupting Odoo UI
if (typeof window !== "undefined" && !window.__ora_krisp_handler_installed) {
    window.__ora_krisp_handler_installed = true;
    window.addEventListener("unhandledrejection", (event) => {
        const err = event.reason;
        const errMsg = String(err?.message || err || '');
        const errName = String(err?.name || '');
        if (errName.includes("Krisp") || errMsg.includes("Krisp") || errMsg.includes("Path not found")) {
            console.warn("Suppressed Krisp noise-cancellation initialization error:", err);
            event.preventDefault();
            if (typeof event.stopImmediatePropagation === "function") {
                event.stopImmediatePropagation();
            }
        }
    });
}


class VoiceAssistant extends Component {
    static components = { VoiceData };
    static template = 'ora_ai_base.voice_assistant';
    props = useProps(standardActionServiceProps);

    setup() {
        const action = this.props?.action || {};
        const params = action.params || this.props?.params || {};
        this.assistantId = params.assistant_id || '';
        this.apiKey = params.api_key || '';
        this.isTestMode = Boolean(params.test_mode);
        this.configInfo = {
            provider: params.provider || '',
            model: params.provider_model || '',
            language: params.language || '',
            transcriber: params.transcriber || '',
        };
        this.state = proxy({
            callState: 'idle', // 'idle' | 'connecting' | 'active' | 'ended' | 'error'
            msg: this.isTestMode
                ? `Click microphone to test ${params.assistant_name || 'Assistant'}`
                : `Click microphone to start ${params.assistant_name || 'Assistant'}`,
            assistant_name: params.assistant_name || 'Assistant',
            volume: 0,
            isSpeaking: false,
        });
        try {
            this.userService = useService("user");
        } catch {
            this.userService = this.env?.services?.user;
        }
        this.vapiReady = false;
        this.vapiInstance = null;
        window.assistant = this.assistantId;
        window.apiKey = this.apiKey;

        // Listener for toggle request from child components
        const handleToggleCall = () => this.toggle_call();
        window.addEventListener("ora_toggle_call", handleToggleCall);

        // Clean up Vapi floating button and stop call when leaving this view
        onWillUnmount(() => {
            window.removeEventListener("ora_toggle_call", handleToggleCall);
            if (this.vapiInstance) {
                try {
                    if (typeof this.vapiInstance.stop === 'function') {
                        this.vapiInstance.stop();
                    }
                    if (typeof this.vapiInstance.destroy === 'function') {
                        this.vapiInstance.destroy();
                    }
                } catch (e) {
                    console.warn("Error stopping VAPI call:", e);
                }
            }
            this.vapiInstance = null;
            window.assistant = null;
            document.querySelectorAll("#vapi-support-btn, .vapi-btn").forEach((el) => {
                try { el.remove(); } catch (e) {}
            });
        });

        // Ensure VAPI SDK is loaded using Odoo's native asset loader
        onWillStart(async () => {
            if (!window.vapiSDK) {
                try {
                    await loadJS("/ora_ai_base/static/src/lib/vapi.min.js");
                } catch (err) {
                    console.error("Failed to load Vapi library via Odoo loadJS:", err);
                }
            }
            this.vapiReady = Boolean(window.vapiSDK && typeof window.vapiSDK.run === 'function');
        });

        onMounted(() => {
            document.querySelectorAll("#vapi-support-btn, .vapi-btn").forEach((el) => {
                try { el.remove(); } catch (e) {}
            });
            if (window.vapiSDK && typeof window.vapiSDK.run === 'function') {
                this.vapiReady = true;
            }
        });
    }

    toggle_call() {
        if (this.state.callState === 'active' || this.state.callState === 'connecting') {
            this.stop_vapi();
        } else {
            this.start_vapi();
        }
    }

    stop_vapi() {
        if (this.vapiInstance) {
            try {
                if (typeof this.vapiInstance.stop === 'function') {
                    this.vapiInstance.stop();
                }
            } catch (e) {
                console.warn("Error stopping VAPI call:", e);
            }
        }
        this.state.callState = 'ended';
        this.state.msg = "Call ended. Click microphone to start again.";
        this.state.volume = 0;
        this.state.isSpeaking = false;
        window.dispatchEvent(new CustomEvent("vapi_status", {
            detail: { callState: 'ended', msg: this.state.msg }
        }));
        window.dispatchEvent(new CustomEvent("vapi_speech", {
            detail: { isSpeaking: false }
        }));
        window.dispatchEvent(new CustomEvent("vapi_volume", {
            detail: { volume: 0 }
        }));
    }

    async start_vapi() {
        const self = this;

        if (!this.vapiReady || !window.vapiSDK || typeof window.vapiSDK.run !== 'function') {
            self.state.msg = "Voice assistant not ready. Please wait...";
            self.state.callState = 'connecting';
            window.dispatchEvent(new CustomEvent("vapi_status", {
                detail: { callState: 'connecting', msg: self.state.msg }
            }));
            console.warn("VAPI SDK is not ready yet.");
            return;
        }

        // Clean up any previously attached floating button
        document.querySelectorAll("#vapi-support-btn, .vapi-btn").forEach((el) => {
            try { el.remove(); } catch (e) {}
        });
        if (self.vapiInstance) {
            try {
                if (typeof self.vapiInstance.stop === 'function') {
                    self.vapiInstance.stop();
                }
                if (typeof self.vapiInstance.destroy === 'function') {
                    self.vapiInstance.destroy();
                }
            } catch (e) {
                // ignore
            }
            self.vapiInstance = null;
        }

        self.state.callState = 'connecting';
        self.state.msg = "Connecting to assistant...";
        window.dispatchEvent(new CustomEvent("vapi_status", {
            detail: { callState: 'connecting', msg: self.state.msg }
        }));

        const action = self.props?.action || {};
        const params = action.params || self.props?.params || {};
        const apiKey = params.api_key || self.apiKey || window.apiKey;
        const assistantId = params.assistant_id || self.assistantId || window.assistant;

        if (!apiKey || !assistantId) {
            const missingMsg = !assistantId
                ? "No Voice Assistant ID found. Please create or save an assistant first."
                : "Vapi Public API Key is missing. Please configure it in Voice Assistant Settings.";
            self.state.callState = 'error';
            self.state.msg = missingMsg;
            window.dispatchEvent(new CustomEvent("vapi_status", {
                detail: {
                    callState: 'error',
                    msg: missingMsg,
                    showErrorPopup: true,
                    errorTitle: "Configuration Missing",
                    errorMessage: missingMsg
                }
            }));
            return;
        }

        const VAPI = await window.vapiSDK.run({
            apiKey: apiKey,
            assistant: assistantId,
        });
        if (!VAPI || typeof VAPI.start !== 'function') {
            self.state.callState = 'error';
            self.state.msg = "Failed to initialize the assistant.";
            window.dispatchEvent(new CustomEvent("vapi_status", {
                detail: { callState: 'error', msg: self.state.msg }
            }));
            console.error("VAPI object is invalid.");
            return;
        }
        self.vapiInstance = VAPI;
        const variableValues = {};
        if (self.isTestMode) {
            variableValues.test_mode = "true";
        }
        const currentUserId = params.user_id ||
            (typeof odoo !== "undefined" && odoo.session_info?.uid) ||
            window.odoo?.session_info?.uid ||
            self.userService?.userId ||
            self.userService?.id ||
            self.env?.services?.user?.userId ||
            self.env?.services?.user?.id ||
            null;
        if (currentUserId) {
            variableValues.salesperson_id = String(currentUserId);
            variableValues.user_id = String(currentUserId);
        }
        const currentPartnerId = params.partner_id ||
            (typeof odoo !== "undefined" && odoo.session_info?.partner_id) ||
            window.odoo?.session_info?.partner_id ||
            self.userService?.partnerId ||
            self.env?.services?.user?.partnerId ||
            null;
        if (currentPartnerId) {
            variableValues.partner_id = String(currentPartnerId);
        }
        const metadata = {};
        if (currentUserId) {
            metadata.salesperson_id = String(currentUserId);
            metadata.user_id = String(currentUserId);
        }
        if (currentPartnerId) {
            metadata.partner_id = String(currentPartnerId);
        }
        const assistantOverrides = {
            variableValues,
            ...(Object.keys(metadata).length > 0 ? { metadata } : {}),
        };

        VAPI.start(assistantId, assistantOverrides);

        VAPI.on("call-start", () => {
            self.state.callState = 'active';
            self.state.msg = "Listening... Speak now";
            window.dispatchEvent(new CustomEvent("vapi_status", {
                detail: { callState: 'active', msg: self.state.msg }
            }));
        });

        VAPI.on("call-end", () => {
            self.state.callState = 'ended';
            self.state.msg = "Thank you for using the assistant.";
            self.state.volume = 0;
            self.state.isSpeaking = false;
            window.dispatchEvent(new CustomEvent("vapi_status", {
                detail: { callState: 'ended', msg: self.state.msg }
            }));
            window.dispatchEvent(new CustomEvent("vapi_speech", {
                detail: { isSpeaking: false }
            }));
            window.dispatchEvent(new CustomEvent("vapi_volume", {
                detail: { volume: 0 }
            }));
        });

        VAPI.on("speech-start", () => {
            self.state.isSpeaking = true;
            window.dispatchEvent(new CustomEvent("vapi_speech", {
                detail: { isSpeaking: true }
            }));
        });

        VAPI.on("speech-end", () => {
            self.state.isSpeaking = false;
            window.dispatchEvent(new CustomEvent("vapi_speech", {
                detail: { isSpeaking: false }
            }));
        });

        VAPI.on("volume-level", (volume) => {
            self.state.volume = volume || 0;
            window.dispatchEvent(new CustomEvent("vapi_volume", {
                detail: { volume: volume || 0 }
            }));
        });

        VAPI.on("message", (message) => {
            if (message.type === "transcript") {
                const prefix = message.role === "user" ? "🧑 Me" : "🤖 Assistant";
                if (message.transcriptType === "partial") {
                    self.state.msg = `${prefix}: ${message.transcript}`;
                }
                if (message.transcriptType === "final") {
                    self.state.msg = `${prefix}: ${message.transcript}`;
                }
            } else if (message.type === "status-update" && message.status === "ended") {
                self.state.callState = 'ended';
                self.state.msg = "Thank you for using the assistant.";
                self.state.volume = 0;
                self.state.isSpeaking = false;
                window.dispatchEvent(new CustomEvent("vapi_status", {
                    detail: { callState: 'ended', msg: self.state.msg }
                }));
                window.dispatchEvent(new CustomEvent("vapi_speech", {
                    detail: { isSpeaking: false }
                }));
                window.dispatchEvent(new CustomEvent("vapi_volume", {
                    detail: { volume: 0 }
                }));
            }
            window.dispatchEvent(new CustomEvent("vapi_message", { detail: message }));
        });

        VAPI.on("error", async (e) => {
            console.error("VAPI Error:", e);

            const rawStr = (() => {
                try {
                    return JSON.stringify(e).toLowerCase();
                } catch {
                    return String(e).toLowerCase();
                }
            })();

            // If the call has already ended or is ending due to meeting closure/ejection/hangup, handle normally without an error popup
            const isCallEndEjection = Boolean(
                self.state.callState === 'ended' ||
                rawStr.includes("meeting has ended") ||
                rawStr.includes("ejected") ||
                rawStr.includes("ejection") ||
                rawStr.includes("left-meeting") ||
                rawStr.includes("customer-ended-call") ||
                rawStr.includes("assistant-ended-call") ||
                rawStr.includes("call-ended") ||
                rawStr.includes("call ended") ||
                rawStr.includes("ended due to ejection") ||
                rawStr.includes("meeting finished") ||
                rawStr.includes("call has ended") ||
                rawStr.includes("hangup") ||
                (e?.type === "daily-error" && (rawStr.includes("ended") || rawStr.includes("eject"))) ||
                e?.errorMsg === "Meeting has ended" ||
                e?.error?.errorMsg === "Meeting has ended" ||
                e?.error?.msg === "Meeting has ended" ||
                e?.error?.error?.msg === "Meeting has ended" ||
                e?.error?.message?.msg === "Meeting has ended" ||
                e?.error?.type === "ejected" ||
                e?.error?.error?.type === "ejected" ||
                e?.error?.message?.type === "ejected" ||
                (typeof e?.message === 'string' && (e.message.toLowerCase().includes("meeting has ended") || e.message.toLowerCase().includes("ejected"))) ||
                (typeof e?.errorMsg === 'string' && (e.errorMsg.toLowerCase().includes("meeting has ended") || e.errorMsg.toLowerCase().includes("ejected")))
            );

            if (isCallEndEjection) {
                self.state.callState = 'ended';
                self.state.msg = "Thank you for using the assistant.";
                self.state.volume = 0;
                self.state.isSpeaking = false;
                window.dispatchEvent(new CustomEvent("vapi_status", {
                    detail: { callState: 'ended', msg: self.state.msg }
                }));
                window.dispatchEvent(new CustomEvent("vapi_speech", {
                    detail: { isSpeaking: false }
                }));
                window.dispatchEvent(new CustomEvent("vapi_volume", {
                    detail: { volume: 0 }
                }));
                return;
            }

            let errMsg = "Something went wrong. Please try again.";
            if (e) {
                if (typeof e === 'string') {
                    errMsg = e;
                } else if (typeof e.message === 'string') {
                    errMsg = e.message;
                } else if (Array.isArray(e.message)) {
                    errMsg = e.message.join("\n");
                } else if (e.message && typeof e.message === 'object') {
                    errMsg = e.message.msg || e.message.message || e.message.error || "";
                } else if (typeof e.errorMsg === 'string') {
                    errMsg = e.errorMsg;
                } else if (e.error) {
                    if (typeof e.error === 'string') {
                        errMsg = e.error;
                    } else if (typeof e.error.message === 'string') {
                        errMsg = e.error.message;
                    } else if (Array.isArray(e.error.message)) {
                        errMsg = e.error.message.join("\n");
                    } else if (typeof e.error.errorMsg === 'string') {
                        errMsg = e.error.errorMsg;
                    } else if (typeof e.error.msg === 'string') {
                        errMsg = e.error.msg;
                    } else if (e.error.error && typeof e.error.error.msg === 'string') {
                        errMsg = e.error.error.msg;
                    } else if (e.error.message && typeof e.error.message === 'object') {
                        errMsg = e.error.message.msg || e.error.message.message || "";
                    }
                } else if (typeof e.json === 'function') {
                    try {
                        const jsonErr = await e.json();
                        if (typeof jsonErr?.message === 'string') {
                            errMsg = jsonErr.message;
                        } else if (Array.isArray(jsonErr?.message)) {
                            errMsg = jsonErr.message.join("\n");
                        } else if (typeof jsonErr?.msg === 'string') {
                            errMsg = jsonErr.msg;
                        }
                    } catch {}
                }
            }

            if (!errMsg || typeof errMsg !== 'string' || errMsg === '[object Object]') {
                errMsg = "Something went wrong. Please try again.";
            }

            let title = "Voice Assistant Error";
            const lowerErr = String(errMsg).toLowerCase();
            if (lowerErr.includes("transcriber") || lowerErr.includes("transcription")) {
                title = "Transcriber Model Unavailable";
                const currentTranscriber = self.configInfo?.transcriber || 'configured transcriber';
                errMsg = `The Transcriber model '${currentTranscriber}' is currently unavailable or rejected by the service.\n\nDetails: ${errMsg}`;
            } else if (lowerErr.includes("model") || lowerErr.includes("provider") || lowerErr.includes("must be one of")) {
                title = "AI Model Unavailable";
                const currentModel = self.configInfo?.model || 'configured model';
                const currentProvider = self.configInfo?.provider || 'provider';
                errMsg = `The AI model '${currentModel}' (${currentProvider}) is currently unavailable or rejected by the service.\n\nDetails: ${errMsg}`;
            } else if (lowerErr.includes("quota") || lowerErr.includes("credit") || lowerErr.includes("billing") || lowerErr.includes("rate limit")) {
                title = "Service Limit / Balance Exhausted";
            }

            self.state.callState = 'error';
            self.state.msg = errMsg;
            window.dispatchEvent(new CustomEvent("vapi_status", {
                detail: { 
                    callState: 'error', 
                    msg: errMsg,
                    showErrorPopup: true,
                    errorTitle: title,
                    errorMessage: errMsg
                }
            }));
        });
    }
}
VoiceAssistant.template = 'ora_ai_base.voice_assistant';
registry.category("actions").add("action_voice_assistant", VoiceAssistant);
