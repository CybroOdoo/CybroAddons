/** @odoo-module **/

import { Component, useState } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";

export class MeetingSubtitles extends Component {
    static template = "meeting_transcription_summary.MeetingSubtitles";
    static props = ["thread?"];

    setup() {
        this.speechService = useService("discuss_meeting_ai.speech");
        // subscribe to the service state, so new captions re-render this component
        this.state = useState(this.speechService.state);
    }
}
