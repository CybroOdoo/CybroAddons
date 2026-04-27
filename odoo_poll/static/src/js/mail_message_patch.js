/** @odoo-module **/

import { patch } from "@web/core/utils/patch";
import { Message } from "@mail/core/common/message";
import { PollMessage } from "@odoo_poll/js/poll_message";

//Extend Message component registry
patch(Message, {
    components: {
        ...Message.components,
        PollMessage,
    },
});

//Patch Message prototype lifecycle
patch(Message.prototype, {
    setup() {
        super.setup();

        const body = this.props.message?.body || "";

        //Captures the numeric poll ID
        const match = body.match(/data-poll-id="(\d+)"/);

        if (match) {
            this.pollId = parseInt(match[1]);
        }
    },
});

