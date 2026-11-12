/** @odoo-module **/

import { Rtc } from "@mail/discuss/call/common/rtc_service";
import { patch } from "@web/core/utils/patch";

patch(Rtc.prototype, {
    async joinCall(channel) {
        const res = await super.joinCall(...arguments);
        if (this.state.channel?.eq(channel)) {
            // Transcription and subtitles are call-wide: pick up what the call already has on.
            this.store?.env?.services?.["discuss_meeting_ai.speech"]?.joinedCall(
                this.state.channel
            );
        }
        return res;
    },

    async leaveCall(channel = this.state.channel) {
        // The transcript is kept on the server and saved once for everyone when the call ends:
        // leaving only stops this participant's microphone capture.
        this.store?.env?.services?.["discuss_meeting_ai.speech"]?.resetMeeting();
        return super.leaveCall(...arguments);
    },
});
