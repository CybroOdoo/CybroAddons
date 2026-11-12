/** @odoo-module **/

import { Component, useState } from "@odoo/owl";
import { Dialog } from "@web/core/dialog/dialog";
import { useService } from "@web/core/utils/hooks";
import { _t } from "@web/core/l10n/translation";

export class UploadRecordingDialog extends Component {
    static components = { Dialog };
    static props = {
        close: Function,
        thread: Object,
    };
    static template = "meeting_transcription_summary.UploadRecordingDialog";

    setup() {
        this.notification = useService("notification");
        this.action = useService("action");

        const channelName = this.props.thread?.displayName || this.props.thread?.name || "";
        const defaultTitle = channelName
            ? _t("Recording: %(channel)s (%(date)s)", {
                  channel: channelName,
                  date: new Date().toLocaleDateString(),
              })
            : _t("Meeting Recording (%s)", new Date().toLocaleDateString());

        this.state = useState({
            file: null,
            title: defaultTitle,
            durationMinutes: 15,
            isUploading: false,
            errorMessage: null,
            success: false,
            successMessage: "",
            summaryId: null,
        });
    }

    get dialogTitle() {
        return _t("Upload Meeting Recording");
    }

    onFileChange(ev) {
        const file = ev.target.files?.[0];
        if (file) {
            this.state.file = file;
            this.state.errorMessage = null;
        }
    }

    async submitUpload() {
        if (!this.state.file) {
            this.state.errorMessage = _t("Please select a video or audio file to upload.");
            return;
        }

        this.state.isUploading = true;
        this.state.errorMessage = null;

        try {
            const formData = new FormData();
            formData.append("channel_id", this.props.thread.id);
            formData.append("csrf_token", odoo.csrf_token);
            formData.append("file", this.state.file);
            formData.append("title", this.state.title || "");
            formData.append("duration_minutes", this.state.durationMinutes || 15);

            const response = await fetch("/discuss/meeting/upload_recording", {
                method: "POST",
                body: formData,
            });

            if (!response.ok) {
                throw new Error(
                    _t("Server error (%(status)s): %(reason)s", {
                        status: response.status,
                        reason: response.statusText,
                    })
                );
            }

            const result = await response.json();
            if (result.status === "success") {
                this.state.success = true;
                this.state.summaryId = result.summary_id;
                this.state.successMessage =
                    result.message ||
                    _t(
                        "Recording uploaded: the summary will be posted to the channel when it is ready."
                    );
                this.notification.add(
                    _t(
                        "Recording uploaded: the summary will be posted to #%s once it is transcribed.",
                        this.props.thread.displayName || this.props.thread.name
                    ),
                    { type: "info" }
                );
            } else {
                this.state.errorMessage =
                    result.error || _t("Failed to transcribe meeting recording.");
            }
        } catch (err) {
            console.error("Error uploading meeting recording:", err);
            this.state.errorMessage =
                err.message || _t("An unexpected error occurred while uploading the file.");
        } finally {
            this.state.isUploading = false;
        }
    }

    openSummaryRecord() {
        if (!this.state.summaryId) {
            return;
        }
        this.action.doAction({
            type: "ir.actions.act_window",
            res_model: "discuss.meeting.summary",
            res_id: this.state.summaryId,
            views: [[false, "form"]],
            target: "current",
        });
        this.props.close();
    }
}
