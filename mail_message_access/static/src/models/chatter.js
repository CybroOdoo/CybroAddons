import { Chatter } from "@mail/chatter/web_portal_project/chatter";
import { patch } from "@web/core/utils/patch";
import { session } from "@web/session";

patch(Chatter.prototype, {
    setup() {
        super.setup();
        this.state.access_send_message_btn = Boolean(session.access_send_message_btn);
        this.state.access_log_note_btn = Boolean(session.access_log_note_btn);
    },
});
