import { browser } from "@web/core/browser/browser";
import { _t } from "@web/core/l10n/translation";
import { RPCError } from "@web/core/network/rpc";
import { registry } from "@web/core/registry";
import { user } from "@web/core/user";
import { useService } from "@web/core/utils/hooks";
import { Component, onWillDestroy, onWillStart, proxy, useListener } from "@odoo/owl";
import { canRecordVoice, MicrophoneError, toVoiceAudio, VoiceRecorder } from "../voice/voice_recorder";

const USER_GROUP = "ai_chat_pro.group_ai_chat_user";
const CONVERSATION_MODEL = "ai.chat.conversation";
const CHAT_ACTION = "ai_chat_pro.ai_chat_action_client";
// how long the question heard is shown before the chat opens, and an error before it hides
const HEARD_DELAY_MS = 700;
const ERROR_DELAY_MS = 3500;

/**
 * Systray button waking the voice assistant, from any screen: it listens to a
 * question, stops when the user stops speaking (or says it is done: background
 * noise can keep the silence from coming), then opens the chat with the
 * question asked in a new conversation. Without voice questions (disabled in the
 * settings, or a browser that can not record), it opens the chat.
 */
export class AiChatSystray extends Component {
    static template = "ai_chat_pro.Systray";

    setup() {
        this.actionService = useService("action");
        this.orm = useService("orm");
        this.state = proxy({
            isAllowed: false,
            // idle, listening, thinking (turning the voice into text), heard, error
            phase: "idle",
            level: 0,
            heard: "",
            error: "",
        });
        this.recorder = null;
        this.voiceEnabled = null;
        onWillStart(async () => {
            this.state.isAllowed = await user.hasGroup(USER_GROUP);
        });
        // captured before the hotkeys: see onKeydown
        useListener(window, "keydown", (ev) => this.onKeydown(ev), { capture: true });
        onWillDestroy(() => {
            this.recorder?.cancel();
            browser.clearTimeout(this.hideTimeout);
        });
    }

    get isActive() {
        return this.state.phase !== "idle";
    }

    get statusText() {
        return {
            listening: _t("Listening..."),
            thinking: _t("One moment..."),
            heard: this.state.heard,
            error: this.state.error,
        }[this.state.phase];
    }

    async onClick() {
        if (this.state.phase === "listening") {
            this.finish();
            return;
        }
        if (this.isActive && this.state.phase !== "error") {
            return;
        }
        if (!(await this.isVoiceEnabled())) {
            this.openChat();
            return;
        }
        await this.listen();
    }

    async isVoiceEnabled() {
        if (this.voiceEnabled === null) {
            const assistant = await this.orm.call(CONVERSATION_MODEL, "get_voice_assistant_state", []);
            this.voiceEnabled = assistant.voice && canRecordVoice();
        }
        return this.voiceEnabled;
    }

    async listen() {
        browser.clearTimeout(this.hideTimeout);
        const recorder = new VoiceRecorder({ autoStop: true, onLevel: (level) => (this.state.level = level) });
        this.recorder = recorder;
        this.setPhase("listening");
        try {
            await recorder.start();
        } catch (error) {
            this.recorder = null;
            if (error instanceof MicrophoneError) {
                this.showError(_t("The microphone cannot be used. Please allow this page to access it."));
                return;
            }
            throw error;
        }
        const blob = await recorder.result;
        this.recorder = null;
        if (!blob) {
            this.setPhase("idle");
            return;
        }
        this.setPhase("thinking");
        let question;
        try {
            const transcription = await this.orm.call(CONVERSATION_MODEL, "transcribe_audio", [
                await toVoiceAudio(blob),
            ]);
            question = transcription.text;
        } catch (error) {
            const message = error instanceof RPCError ? error.data?.message || error.message : "";
            this.showError(message || _t("The recording could not be read. Please try again."));
            if (!(error instanceof RPCError) && !(error instanceof DOMException)) {
                throw error;
            }
            return;
        }
        if (!question) {
            this.showError(_t("I didn't catch that. Tap to try again."));
            return;
        }
        this.state.heard = question;
        this.setPhase("heard");
        await new Promise((resolve) => browser.setTimeout(resolve, HEARD_DELAY_MS));
        this.setPhase("idle");
        this.openChat({ key: `${Date.now()}`, text: question });
    }

    /**
     * The question is complete: send what was recorded without waiting for the
     * silence, which a noisy room may never give.
     */
    finish() {
        if (this.state.phase === "listening") {
            this.recorder?.stop();
        }
    }

    cancel() {
        browser.clearTimeout(this.hideTimeout);
        if (this.recorder) {
            this.recorder.cancel();
        } else {
            this.setPhase("idle");
        }
    }

    showError(message) {
        this.state.error = message;
        this.setPhase("error");
        this.hideTimeout = browser.setTimeout(() => {
            if (this.state.phase === "error") {
                this.setPhase("idle");
            }
        }, ERROR_DELAY_MS);
    }

    /**
     * While the assistant is shown, Escape closes it, and while it listens, Enter
     * finishes the question. The panel covers the screen like a dialog, so it takes
     * these keys first, from the capture phase: as hotkeys, the newest registration
     * wins, and the screen behind (a list unselecting its records on Escape...) can
     * register its own after the assistant woke up.
     *
     * @param {KeyboardEvent} ev
     */
    onKeydown(ev) {
        if (!this.isActive || ev.isComposing || ev.ctrlKey || ev.altKey || ev.metaKey) {
            return;
        }
        if (ev.key === "Escape") {
            this.cancel();
        } else if (ev.key === "Enter" && this.state.phase === "listening") {
            this.finish();
        } else {
            return;
        }
        ev.preventDefault();
        ev.stopImmediatePropagation();
    }

    setPhase(phase) {
        this.state.phase = phase;
    }

    /**
     * Open the chat full screen; with the question heard, asked in a new chat.
     */
    openChat(voiceQuestion) {
        this.actionService.doAction(CHAT_ACTION, voiceQuestion ? { props: { voiceQuestion } } : {});
    }
}

registry.category("systray").add("ai_chat_pro.systray", { Component: AiChatSystray }, { sequence: 30 });
