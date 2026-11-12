/** @odoo-module **/

import { Component, markup, onWillStart, useState } from "@odoo/owl";
import { Dialog } from "@web/core/dialog/dialog";
import { useService } from "@web/core/utils/hooks";
import { rpc } from "@web/core/network/rpc";
import { _t } from "@web/core/l10n/translation";

export class MeetingSummaryDialog extends Component {
    static components = { Dialog };
    static props = {
        close: Function,
        channel: Object,
    };
    static template = "meeting_transcription_summary.MeetingSummaryDialog";

    setup() {
        this.speechService = useService("discuss_meeting_ai.speech");
        this.notification = useService("notification");
        this.state = useState({
            activeTab: "summary",
            isLoading: false,
            summaryData: null,
            generatedSummaryId: null,
            isPosted: false,
            transcriptLines: [], // [{ id, time, speaker, text }] from the call's shared meeting
            isTranscribing: false,
        });
        onWillStart(() => this.loadTranscript());
    }

    get channelId() {
        return this.props.channel?.id || this.speechService.state.activeChannelId;
    }

    async loadTranscript() {
        try {
            const res = await rpc("/discuss/meeting/transcript", { channel_id: this.channelId });
            if (!res.error) {
                this.state.transcriptLines = res.lines;
                this.state.isTranscribing = res.transcribe;
            }
        } catch {
            // the dialog shows no transcript yet: reopening it loads it again
        }
    }

    get formattedTranscript() {
        return this.state.transcriptLines
            .map((line) => `[${line.time}] ${line.speaker}: ${line.text}`)
            .join("\n");
    }

    async generateSummary() {
        this.state.isLoading = true;
        try {
            await this.loadTranscript();
            const res = await rpc("/discuss/meeting/summarize", { channel_id: this.channelId });

            if (res.status === "success") {
                // sanitized server-side (Html field), so it is rendered as HTML
                this.state.summaryData = {
                    ...res,
                    executive_summary: markup(res.executive_summary || ""),
                };
                this.state.generatedSummaryId = res.summary_id;
                this.state.isPosted = false;
                this.notification.add(_t("AI Meeting Summary successfully generated!"), {
                    type: "success",
                });
            } else {
                this.notification.add(res.error || _t("Could not generate the summary."), {
                    type: "warning",
                });
            }
        } catch (err) {
            console.error("Summarization failed:", err);
            this.notification.add(_t("Failed to contact summarization service."), {
                type: "danger",
            });
        } finally {
            this.state.isLoading = false;
        }
    }

    async postToChannel() {
        if (!this.state.generatedSummaryId) {
            return;
        }
        try {
            const res = await rpc("/discuss/meeting/post_summary", {
                summary_id: this.state.generatedSummaryId,
            });
            if (res?.error) {
                this.notification.add(res.error, { type: "warning" });
                return;
            }
            this.state.isPosted = true;
            this.notification.add(_t("Meeting summary posted to the channel chatter!"), {
                type: "success",
            });
        } catch (err) {
            console.error("Posting summary failed:", err);
            this.notification.add(_t("Could not post summary to channel."), { type: "danger" });
        }
    }

    copyTranscript() {
        const text = this.formattedTranscript;
        if (!text) {
            return;
        }
        navigator.clipboard.writeText(text);
        this.notification.add(_t("Transcript copied to clipboard!"), { type: "info" });
    }
}
