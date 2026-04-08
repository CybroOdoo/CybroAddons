/* @odoo-module */
import { Chatter } from "@mail/chatter/web_portal/chatter";
import { patch } from "@web/core/utils/patch";
import { rpc } from "@web/core/network/rpc";

patch(Chatter.prototype, {
    async setup() {
        super.setup();
        var data =await rpc("/web/session/get_session_info");
        this.state.access_send_message_btn=false
        this.state.access_log_note_btn=false
        this.state.access_send_message_btn = data.access_send_message_btn
        this.state.access_log_note_btn = data.access_log_note_btn
    },
});
