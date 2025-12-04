/* @odoo-module */
import { patch } from "@web/core/utils/patch";
import { CallActionList } from "@mail/discuss/call/common/call_action_list";
import { useService } from "@web/core/utils/hooks";
import { useState, useEffect } from "@odoo/owl";
import { rpc } from "@web/core/network/rpc";
import { user } from "@web/core/user";

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
            // Request audio permissions explicitly
            const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
            // Keep track of the stream to ensure it stays active
            this.audioStream = stream;
            this.recognition = new SpeechRecognition();
            this.recognition.continuous = true;
            this.recognition.interimResults = true;
            this.recognition.lang = 'en-US';
            this.setupEventListeners();
            this.isInitialized = true;
        } catch (error) {
            console.error("Error initializing speech recognition:", error);
            this.shouldRestart = false;
            // Provide more specific error feedback
            if (error.name === 'NotAllowedError') {
                console.error("Microphone permission denied. Please enable microphone access.");
            }
        }
    }

    setupEventListeners() {
        this.recognition.onerror = (event) => {
            console.error("Speech Recognition Error:", event.error, event);
            if (event.error === 'not-allowed') {
                this.shouldRestart = false;
                console.error("Microphone permission denied");
            } else if (event.error === 'audio-capture') {
                this.shouldRestart = false;
                console.error("No microphone detected");
            } else if (this.shouldRestart && this.active) {
                // Use exponential backoff for retries
                const delay = Math.min(2000, 1000 * Math.pow(1.5, this.errorCount || 0));
                this.errorCount = (this.errorCount || 0) + 1;
                setTimeout(() => this.restartRecognition(), delay);
            }
        };

        this.recognition.onend = () => {
            this.recognitionActive = false;
            // Process any remaining buffered text
            if (this.bufferText.trim()) {
                this.transcriptionHandler({
                    text: this.bufferText.trim(),
                    userId: this.user?.id,
                    timestamp: new Date().toISOString()
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
            let interimTranscript = "";
            let hasFinal = false;

            // Process all results since last event
            for (let i = event.resultIndex; i < event.results.length; i++) {
                const transcript = event.results[i][0].transcript;

                if (event.results[i].isFinal) {
                    finalTranscript += transcript;
                    hasFinal = true;
                } else {
                    interimTranscript += transcript;
                }
            }

            // Handle final results
            if (hasFinal && finalTranscript.trim()) {
                this.bufferText += finalTranscript;

                // Send complete utterances
                const completeUtterances = this.extractCompleteUtterances(this.bufferText);
                if (completeUtterances) {
                    this.transcriptionHandler({
                        text: completeUtterances,
                        userId: this.user?.id,
                        timestamp: new Date().toISOString()
                    });

                    // Remove sent utterances from buffer
                    this.bufferText = this.bufferText.slice(completeUtterances.length);
                }
            }

            // Reset silence timer on any speech
            if (this.silenceTimer) {
                clearTimeout(this.silenceTimer);
            }

            // Set silence timer to send remaining buffer after pause
            this.silenceTimer = setTimeout(() => {
                if (this.bufferText.trim()) {
                    this.transcriptionHandler({
                        text: this.bufferText.trim(),
                        userId: this.user?.id,
                        timestamp: new Date().toISOString()
                    });
                    this.bufferText = "";
                }
            }, 2000); // 2 second silence sends buffer
        };
    }

    // Helper to extract complete utterances (ending with punctuation)
    extractCompleteUtterances(text) {
        if (!text) return "";

        // Find the last occurrence of sentence-ending punctuation
        const match = text.match(/[.!?]\s*(?=[A-Z]|$)/);
        if (!match) return "";

        const endPos = match.index + 1;
        return text.substring(0, endPos + 1).trim();
    }

    async restartRecognition() {
        if (!this.active || !this.shouldRestart) return;
        try {
            // Only stop if actually running
            if (this.recognitionActive) {
                try {
                    await this.recognition.stop();
                    // Wait for onend event to complete
                    await new Promise(resolve => {
                        const checkActive = () => {
                            if (!this.recognitionActive) {
                                resolve();
                            } else {
                                setTimeout(checkActive, 100);
                            }
                        };
                        checkActive();
                    });
                } catch (error) {
                    console.log("Error stopping recognition:", error);
                }
            }

            // Small delay to ensure complete shutdown
            await new Promise(resolve => setTimeout(resolve, 500));

            // Only try to start if we're still supposed to be active
            if (this.active && this.shouldRestart) {
                await this.recognition.start();
            }
        } catch (error) {
            console.error("Error in restartRecognition:", error);

            // Try again after a longer delay if we're still supposed to be active
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
            this.bufferText = ""; // Clear any previous buffer
            this.errorCount = 0;

            try {
                // Only start if not already running
                if (!this.recognitionActive) {
                    await this.recognition.start();
                } else {
                    console.log("Recognition already active, not starting again");
                }
            } catch (error) {
                if (error.name === 'NotAllowedError') {
                    this.shouldRestart = false;
                    // Request permissions again
                    try {
                        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
                        this.audioStream = stream;
                        // Try starting again after permission granted
                        setTimeout(() => this.start(), 1000);
                    } catch (permError) {
                        console.error("Permission request failed:", permError);
                    }
                } else if (this.active) {
                    // Try again after a delay
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

        // Process any remaining buffer
        if (this.bufferText.trim()) {
            this.transcriptionHandler({
                text: this.bufferText.trim(),
                userId: this.user?.id,
                timestamp: new Date().toISOString()
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

        // Release audio stream if it exists
        if (this.audioStream) {
            this.audioStream.getTracks().forEach(track => track.stop());
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

patch(CallActionList.prototype, {
    async setup() {
        super.setup(...arguments);
        try {
            this.action = useService("action");
            this.user = user;
        } catch (error) {
            console.warn("Service 'action' is not available for guest users.");
            this.action = null; // Fallback for guests
            this.user = null; // Fallback for guests
        }

        this.state = useState({
            isRecording: false,
            transcriptions: {},
            currentSpeaker: null,
            userName: null,
        });

        useEffect(() => {
            this.speechQueue = new SpeechRecognitionQueue(
                this.insertTranscription.bind(this),
                this.user
            );
            this.initializeUserInfo();

            // Cleanup function for when component is destroyed
            return () => {
                if (this.speechQueue) {
                    this.speechQueue.stop();
                }
            };
        }, () => []);

        useEffect(() => {
            try {
                const hasMultipleMembers = this.props.thread &&
                    this.props.thread.channelMembers &&
                    this.props.thread.channelMembers.length > 0;


                if (hasMultipleMembers && !this.state.isRecording) {
                    this.startRecording();
                } else if (!hasMultipleMembers && this.state.isRecording) {
                    this.stopRecording();
                }
            } catch (error) {
                console.error("Error in channel members effect:", error);
            }
        }, () => [this.props.thread?.channelMembers?.length]);
    },

    async onClickMicrophone(ev) {
        await super.onClickMicrophone(ev);

        try {
            if (this.rtc?.state?.selfSession?.isMute) {
                this.stopRecording();
            } else {
                this.startRecording();
            }
        } catch (error) {
            console.error("Error handling microphone click:", error);
        }
    },

    async initializeUserInfo() {
        try {
            let userName = "Unknown User"; // Default fallback

            // Try multiple methods to get user name
            if (this?.user?.name) {
                userName = this.user.name;
            } else if (this?.__owl__?.parent?.parent?.children?.__11?.component?.state?.value) {
                userName = this.__owl__.parent.parent.children.__11.component.state.value;
            }

            this.state.userName = userName;
        } catch (error) {
            console.error("Error initializing user info:", error);
            this.state.userName = "Unknown User"; // Fallback
        }
    },

    async CreateTranscriptionFile() {
        try {
            if (!this.props.thread || !this.props.thread.id) {
                console.error("Cannot create transcription file: thread or thread ID is missing");
                return;
            }

            const fileName = `transcription_${this.props.thread.id}.txt`;
            const Id = this.props.thread.id;

            const response = await rpc('/create/transcription_file_summary', {
                kwargs: { id: Id }
            });
        } catch (error) {
            console.error("Error creating transcription file:", error);
        }
    },

    async onClickToggleAudioCall(ev) {
        try {
            const buttonDis = document.querySelector('[aria-label="Disconnect"]');
            const res = await super.onClickToggleAudioCall(ev);
            if (!this.props.thread) {
                console.error("Thread is undefined in onClickToggleAudioCall");
                return res;
            }

            const subject = this.props.thread.description || " ";
            await this.CreateTranscriptionFile();

            setTimeout(async () => {
                try {
                    const result = await rpc('/get/transcription_data/summary', {
                        kwargs: {
                            channelId: this.props.thread.id,
                        },
                    });

                    const MeetingAdmin = await rpc('/get/Meeting/creator', {
                        kwargs: {
                            channelId: this.props.thread.id,
                        },
                    });
                    if ((this.user?.userId == MeetingAdmin) && buttonDis && result?.transcriptionId && result?.summaryId) {
                        try {
                            this.stopRecording();

                            const partner_details = await rpc('/check/auto_mail_send', {
                                kwargs: {
                                    channelId: this.props.thread.id,
                                },
                            });

                            const partnerIds = partner_details.map(p => p.partner_id);

                            const transcriptionId = await rpc('/create/send_transcription/record', {
                                kwargs: {
                                    partnerIds: partnerIds,
                                    subject: subject,
                                    email_body: "<p>Meeting content here...</p>",
                                    transcriptionId: result.transcriptionId,
                                    summaryId: result.summaryId,
                                },
                            });

                            if (partner_details.length != 0) {
                                const partners_email = partner_details.map(p => p.email);

                                const emailResponse = await rpc('/send/auto_email', {
                                    kwargs: {
                                        partners_email: partners_email,
                                        subject: subject,
                                        email_body: "<p>Meeting content here...</p>",
                                        transcriptionId: result.transcriptionId,
                                        summaryId: result.summaryId,
                                    },
                                });

                            } else {
                                await this.tryOpeningTranscription(transcriptionId);
                            }
                        } catch (error) {
                            console.error("Error in admin meeting end processing:", error);
                        }
                    }
                } catch (error) {
                    console.error("Error in transcription processing timeout:", error);
                }
            }, 500);

            return res;
        } catch (error) {
            console.error("Error in onClickToggleAudioCall:", error);
            return false;
        }
    },

    async tryOpeningTranscription(transcriptionId) {
        if (!this.action) {
            console.error("Error: this.action is undefined.");
            return;
        }

        try {
            const actionData = {
                name: "Send mail Transcription",
                type: "ir.actions.act_window",
                res_model: "send.mail.transcription",
                res_id: transcriptionId,
                view_mode: "form",
                views: [[false, "form"]],  // Ensures proper view format
                target: "new",
            };

            await this.action.doAction(actionData);
        } catch (error) {
            console.error("Error in doAction:", error);
        }
    },

    async startRecording() {
        try {
            if (!this.speechQueue) {
                this.speechQueue = new SpeechRecognitionQueue(
                    this.insertTranscription.bind(this),
                    this.user
                );
            }

            await this.speechQueue.start();
            this.state.isRecording = true;
            this.state.currentSpeaker = this.state.userName || (this.user?.name || "Unknown User");

            if (!this.state.transcriptions[this.state.currentSpeaker]) {
                this.state.transcriptions[this.state.currentSpeaker] = [];
            }

        } catch (error) {
            console.error("Error starting recording:", error);
            this.state.isRecording = false;
        }
    },

    async insertTranscription(transcriptionData) {
        const { text, userId, timestamp } = transcriptionData;

        let speakerName = "Unknown User";

        // Try multiple methods to get speaker name
        if (this.state.userName) {
            speakerName = this.state.userName;
        } else if (this.user && this.user.name) {
            speakerName = this.user.name;
        }

        const formattedText = `(${new Date(timestamp).toLocaleString()})\n\t${speakerName} : ${text}\n`;

        try {
            if (!this.props.thread || !this.props.thread.id) {
                console.error("Cannot send transcription: thread or thread ID is missing");
                return;
            }

            const response = await rpc('/get/transcription_data', {
                data: formattedText,
                id: this.props.thread.id,
                userId: userId,
                timestamp: timestamp
            });

        } catch (error) {
            console.error("Error sending transcription:", error);
        }
    },

    async stopRecording() {

        if (this.state.isRecording) {
            if (this.speechQueue) {
                this.speechQueue.stop();
            }
            this.state.isRecording = false;
        }

        try {
            if (!this.props.thread || !this.props.thread.id) {
                console.error("Cannot attach transcription: thread or thread ID is missing");
                return;
            }

            await rpc('/attach/transcription_data/summary', {
                kwargs: {
                    channelId: this.props.thread.id,
                },
            });

        } catch (error) {
            console.error("Error attaching transcription data:", error);
        }
    },
});