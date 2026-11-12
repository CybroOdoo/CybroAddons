/** @odoo-module **/

import { registerCallAction } from "@mail/discuss/call/common/call_actions";
import { ACTION_TAGS } from "@mail/core/common/action";
import { _t } from "@web/core/l10n/translation";
import { MeetingSummaryDialog } from "./meeting_summary_dialog";

function getSpeech({ store, owner }) {
    return (
        store?.env?.services?.["discuss_meeting_ai.speech"] ||
        owner?.env?.services?.["discuss_meeting_ai.speech"]
    );
}

export const meetingSubtitlesAction = {
    condition: ({ thread }) => Boolean(thread?.isSelfInCall),
    name: (ctx) =>
        getSpeech(ctx)?.state?.subtitlesEnabled ? _t("Subtitle(CC): On") : _t("Subtitle(CC): Off"),
    isActive: (ctx) => Boolean(getSpeech(ctx)?.state?.subtitlesEnabled),
    isTracked: true,
    icon: "fa fa-cc",
    onSelected: (ctx) => getSpeech(ctx)?.toggleSubtitles(ctx.thread || ctx.store?.rtc?.channel),
    sequence: 65,
    sequenceGroup: 200,
    tags: ({ action }) => (action?.isActive ? [ACTION_TAGS.SUCCESS] : []),
};

registerCallAction("meeting-subtitles", meetingSubtitlesAction);

export const meetingTranscribeAction = {
    // only internal users may start or stop transcription (checked by the server too)
    condition: ({ store, thread }) =>
        Boolean(thread?.isSelfInCall) && store?.self_partner?.main_user_id?.share === false,
    name: (ctx) =>
        getSpeech(ctx)?.state?.transcribeEnabled ? _t("Stop Transcribing") : _t("Transcribe"),
    isActive: (ctx) => Boolean(getSpeech(ctx)?.state?.transcribeEnabled),
    isTracked: true,
    icon: "fa fa-file-text-o",
    onSelected: (ctx) => getSpeech(ctx)?.toggleTranscribe(ctx.thread || ctx.store?.rtc?.channel),
    sequence: 66,
    sequenceGroup: 200,
    tags: ({ action }) => (action?.isActive ? [ACTION_TAGS.DANGER] : []),
};

registerCallAction("meeting-transcribe", meetingTranscribeAction);

export const meetingSummaryAction = {
    // summaries are for internal users only (server routes and access rights): not guests or portal users
    condition: ({ store, thread }) =>
        Boolean(thread?.isSelfInCall) && store?.self_partner?.main_user_id?.share === false,
    name: _t("AI Summary & Notes"),
    icon: "fa fa-magic",
    onSelected: ({ owner, store, thread }) => {
        const dialog = store?.env?.services?.dialog || owner?.env?.services?.dialog;
        if (dialog) {
            dialog.add(MeetingSummaryDialog, {
                channel: thread || store?.rtc?.channel,
            });
        }
    },
    sequence: 67,
    sequenceGroup: 200,
};

registerCallAction("meeting-summary", meetingSummaryAction);
