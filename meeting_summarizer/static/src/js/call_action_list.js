/* @odoo-module */
import { patch } from "@web/core/utils/patch";
import { Rtc } from "@mail/discuss/call/common/rtc_service";
import { rpc } from "@web/core/network/rpc";
import { user } from "@web/core/user";
// ---------------------------------------------------------------------------
// Speech-recognition queue (unchanged from the previous version)
// ---------------------------------------------------------------------------

class SpeechRecognitionQueue {
    constructor(transcriptionHandler, user) {
        this.transcriptionHandler = transcriptionHandler;
        this.shouldRestart = true;
        this.user = user;
        this.isInitialized = false;
        this.active = false;
        this.silenceTimer = null;
        this.bufferText = "";
        this.isFinal = false;
        this.stopCall = false;
        this.recognitionActive = false;
    }

    async initSpeechRecognition() {
        if (this.isInitialized) return;

        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        if (!SpeechRecognition) {
            console.warn("Speech Recognition not supported in this browser");
            return;
        }

        try {
            const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
            this.audioStream = stream;
            this.recognition = new SpeechRecognition();
            this.recognition.continuous = true;
            this.recognition.interimResults = true;
            this.recognition.lang = "en-US";
            this.setupEventListeners();
            this.isInitialized = true;
        } catch (error) {
            console.error("Error initializing speech recognition:", error);
            this.shouldRestart = false;
            if (error.name === "NotAllowedError") {
                console.error("Microphone permission denied.");
            }
        }
    }

    setupEventListeners() {
        this.recognition.onerror = (event) => {
            console.error("Speech Recognition Error:", event.error, event);
            if (event.error === "not-allowed") {
                this.shouldRestart = false;
            } else if (event.error === "audio-capture") {
                this.shouldRestart = false;
            }
        };

        this.recognition.onend = () => {
            this.recognitionActive = false;
            // Process any remaining buffered text
            if (this.bufferText.trim()) {
                this.transcriptionHandler({
                    text: this.bufferText.trim(),
                    userId: this.user?.userId,
                    timestamp: new Date().toISOString(),
                });
                this.bufferText = "";
            }

            if (this.shouldRestart && this.active) {
                // Add a small delay before restarting
                setTimeout(() => this.restartRecognition(), 300);
            }
        };

        this.recognition.onstart = () => {
            this.recognitionActive = true;
            this.errorCount = 0; // Reset error count on successful start
        };

        this.recognition.onresult = (event) => {
            let finalTranscript = "";
            let hasFinal = false;

            for (let i = event.resultIndex; i < event.results.length; i++) {
                const transcript = event.results[i][0].transcript;
                if (event.results[i].isFinal) {
                    finalTranscript += transcript;
                    hasFinal = true;
                }
            }

            if (hasFinal && finalTranscript.trim()) {
                this.bufferText += finalTranscript;
                const completeUtterances = this.extractCompleteUtterances(this.bufferText);
                if (completeUtterances) {
                    this.transcriptionHandler({
                        text: completeUtterances,
                        userId: this.user?.userId,
                        timestamp: new Date().toISOString(),
                    });
                    this.bufferText = this.bufferText.slice(completeUtterances.length);
                }
            }

            if (this.silenceTimer) clearTimeout(this.silenceTimer);
            this.silenceTimer = setTimeout(() => {
                if (this.bufferText.trim()) {
                    this.transcriptionHandler({
                        text: this.bufferText.trim(),
                        userId: this.user?.userId,
                        timestamp: new Date().toISOString(),
                    });
                    this.bufferText = "";
                }
            }, 2000); // 2 second silence sends buffer
        };
    }

    extractCompleteUtterances(text) {
        if (!text) return "";
        const match = text.match(/[.!?]\s*(?=[A-Z]|$)/);
        if (!match) return "";
        const endPos = match.index + 1;
        return text.substring(0, endPos + 1).trim();
    }

    async restartRecognition() {
        if (!this.active || !this.shouldRestart) return;
        try {
            if (this.recognitionActive) {
                try {
                    await this.recognition.stop();
                    await new Promise((resolve) => {
                        const checkActive = () => {
                            if (!this.recognitionActive) resolve();
                            else setTimeout(checkActive, 100);
                        };
                        checkActive();
                    });
                } catch (error) {
                    console.log("Error stopping recognition:", error);
                }
            }
            await new Promise((resolve) => setTimeout(resolve, 500));
            if (this.active && this.shouldRestart) {
                await this.recognition.start();
            }
        } catch (error) {
            console.error("Error in restartRecognition:", error);
            if (this.active && this.shouldRestart) {
                setTimeout(() => this.restartRecognition(), 2000);
            }
        }
    }

    async start() {
        if (!this.isInitialized) {
            await this.initSpeechRecognition();
        }
        if (this.recognition) {
            this.shouldRestart = true; // Reset the flag when starting
            this.active = true;
            this.bufferText = "";
            this.errorCount = 0;
            try {
                if (!this.recognitionActive) {
                    await this.recognition.start();
                }
            } catch (error) {
                if (error.name === "NotAllowedError") {
                    this.shouldRestart = false;
                    try {
                        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
                        this.audioStream = stream;
                        setTimeout(() => this.start(), 1000);
                    } catch (permError) {
                        console.error("Permission request failed:", permError);
                    }
                } else if (this.active) {
                    setTimeout(() => this.start(), 1000);
                }
            }
        } else {
            console.error("Recognition not initialized properly");
        }
    }

    stop() {
        this.active = false;
        this.stopCall = true;
        this.shouldRestart = false; // This prevents restarting

        if (this.silenceTimer) {
            clearTimeout(this.silenceTimer);
            this.silenceTimer = null;
        }
        if (this.bufferText.trim()) {
            this.transcriptionHandler({
                text: this.bufferText.trim(),
                userId: this.user?.userId,
                timestamp: new Date().toISOString(),
            });
            this.bufferText = "";
        }
        if (this.recognition && this.recognitionActive) {
            try {
                this.recognition.stop();
            } catch (error) {
                console.error("Error stopping recognition:", error);
            }
        }
        if (this.audioStream) {
            this.audioStream.getTracks().forEach((track) => track.stop());
            this.audioStream = null;
        }
    }

    reset() {
        this.shouldRestart = true;
        this.active = false;
        this.bufferText = "";
        this.errorCount = 0;

        if (this.silenceTimer) {
            clearTimeout(this.silenceTimer);
            this.silenceTimer = null;
        }

        // Stop any active recognition
        if (this.recognition && this.recognitionActive) {
            try {
                this.recognition.stop();
            } catch (error) {
                console.error("Error stopping recognition during reset:", error);
            }
        }
    }
}

// ---------------------------------------------------------------------------
// Per-channel recorder registry (singleton, not tied to any component)
// ---------------------------------------------------------------------------

/** Map<channelId, SpeechRecognitionQueue> */
const _recorders = new Map();

async function _insertTranscription(transcriptionData, channelId) {
    const { text, userId, timestamp } = transcriptionData;
    const formattedText = `(${new Date(timestamp).toLocaleString()})\n\t${user.name || "Unknown User"
        } : ${text}\n`;
    try {
        await rpc("/get/transcription_data", {
            data: formattedText,
            id: channelId,
            userId,
            timestamp,
        });
    } catch (error) {
        console.error("Error sending transcription:", error);
    }
}

async function startChannelRecording(channelId) {
    if (_recorders.has(channelId)) return; // already recording
    const queue = new SpeechRecognitionQueue(
        (data) => _insertTranscription(data, channelId),
        user
    );
    _recorders.set(channelId, queue);
    await queue.start();
}

async function stopChannelRecording(channelId, actionService) {
    // Stop and clean up the speech recognition queue (if active)
    const queue = _recorders.get(channelId);
    if (queue) {
        queue.stop();
        _recorders.delete(channelId);
    }

    // Check if current user is the creator or an administrator
    let MeetingAdmin = false;
    try {
        MeetingAdmin = await rpc("/get/Meeting/creator", {
            channelId,
        });
    } catch (error) {
        console.error("Error fetching meeting creator:", error);
    }

    console.log("[MeetingSummarizer] Creator uid:", MeetingAdmin, "| Current user.userId:", user.userId);

    if (user.userId !== MeetingAdmin) {
        console.log("[MeetingSummarizer] Not the creator – skipping transcription generation and mail flow.");
        return;
    }

    let transcriptionId = false;
    let summaryId = false;

    // ── Step 1: Process raw speech chunks → call OpenAI → create ir.attachment records
    try {
        const result = await rpc("/create/transcription_file_summary", {
            id: channelId,
        });
        if (result?.transcriptionId && result?.summaryId) {
            transcriptionId = result.transcriptionId;
            summaryId = result.summaryId;
            console.log("[MeetingSummarizer] Generated Attachments directly:", transcriptionId, summaryId);
        }
    } catch (error) {
        console.error("Error creating transcription/summary files:", error);
    }

    // Fallback: If not returned directly, fetch them via name-based query
    if (!transcriptionId || !summaryId) {
        try {
            const result = await rpc("/get/transcription_data/summary", {
                channelId,
            });
            transcriptionId = result?.transcriptionId;
            summaryId = result?.summaryId;
            console.log("[MeetingSummarizer] Fetched Attachments from DB:", transcriptionId, summaryId);
        } catch (error) {
            console.error("Error fetching transcription/summary attachment IDs:", error);
        }
    }

    if (!transcriptionId || !summaryId) {
        console.log("[MeetingSummarizer] No transcription or summary files generated (empty speech cache) – aborting.");
        return;
    }

    // ── Step 2: Post the attachments as a channel message (OdooBot posts it)
    try {
        await rpc("/attach/transcription_data/summary", {
            channelId,
            transcriptionId,
            summaryId,
        });
    } catch (error) {
        console.error("Error attaching transcription to channel:", error);
    }

    // ── Step 3: Post-call mail logic
    try {

        const partnerDetails = await rpc("/check/auto_mail_send", {
            channelId,
        });
        console.log("[MeetingSummarizer] partnerDetails:", partnerDetails, "| auto-send recipients:", partnerDetails.length);

        if (partnerDetails.length === 0) {
            // Auto-send is OFF or no recipients configured → open the wizard.
            console.log("[MeetingSummarizer] Auto-send OFF – opening Send Mail wizard.");
            const wizardId = await rpc("/create/send_transcription/record", {
                partnerIds: [],
                subject: "",
                email_body: "<p>Meeting content here...</p>",
                transcriptionId,
                summaryId,
            });
            console.log("[MeetingSummarizer] wizardId:", wizardId, "| actionService:", actionService);

            if (wizardId) {
                // Try actionService first; fall back to the global odoo action service.
                const svc = actionService
                    || window.__owl__?.apps?.values()?.next()?.value?.env?.services?.action
                    || null;
                if (svc) {
                    await svc.doAction({
                        name: "Send Mail Transcription",
                        type: "ir.actions.act_window",
                        res_model: "send.mail.transcription",
                        res_id: wizardId,
                        view_mode: "form",
                        views: [[false, "form"]],
                        target: "new",
                    });
                } else {
                    console.error("[MeetingSummarizer] actionService unavailable – cannot open wizard.");
                }
            }
        } else {
            // Auto-send is ON → email all configured recipients directly.
            console.log("[MeetingSummarizer] Auto-send ON – sending email to", partnerDetails.length, "recipient(s).");
            const partnersEmail = partnerDetails.map((p) => p.email);
            await rpc("/send/auto_email", {
                partners_email: partnersEmail,
                subject: "",
                email_body: "<p>Meeting content here...</p>",
                transcriptionId,
                summaryId,
            });
            console.log("[MeetingSummarizer] Auto-email sent.");
        }
    } catch (error) {
        console.error("[MeetingSummarizer] Error in post-call processing:", error);
    }
}

// ---------------------------------------------------------------------------
// Patch Rtc Record – intercept toggleMicrophone(), leaveCall(), joinCall()
// ---------------------------------------------------------------------------

patch(Rtc.prototype, {
    /**
     * Override toggleMicrophone: start/stop speech recording based on mute state.
     * Called after super so we can read the resulting isMute state.
     */
    async toggleMicrophone() {
        await super.toggleMicrophone(...arguments);
        const channel = this.state?.channel;
        if (!channel) return;
        const channelId = channel.id;
        const isMuted = this.selfSession?.isMute;
        try {
            if (isMuted) {
                // Just muted → pause recording
                const queue = _recorders.get(channelId);
                if (queue) queue.stop();
            } else {
                // Unmuted → resume recording
                await startChannelRecording(channelId);
            }
        } catch (error) {
            console.error("Meeting summarizer: toggleMicrophone hook error:", error);
        }
    },

    /**
     * Override leaveCall: stop recording and run post-call mail flow.
     * Passes the action service so the Send Mail wizard can be opened if needed.
     */
    async leaveCall(channel) {
        const channelId = (channel ?? this.state?.channel)?.id;
        // Run super first so Odoo cleans up its RTC state
        const result = await super.leaveCall(...arguments);
        if (channelId) {
            try {
                const actionService = this.store.env.services?.action;
                await stopChannelRecording(channelId, actionService);
            } catch (error) {
                console.error("Meeting summarizer: leaveCall hook error:", error);
            }
        }
        return result;
    },

    /**
     * Override joinCall: always start recording immediately when joining a call.
     * Recording starts regardless of current member count — the user just joined
     * so we want to capture everything from the beginning.
     */
    async joinCall(channel, options) {
        const result = await super.joinCall(...arguments);
        const channelId = channel?.id;
        if (!channelId) return result;
        try {
            await startChannelRecording(channelId);
        } catch (error) {
            console.error("Meeting summarizer: joinCall hook error:", error);
        }
        return result;
    },
});