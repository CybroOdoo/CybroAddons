import { patch } from "@web/core/utils/patch";
import { Message } from "@mail/core/common/message";
import { PollMessage } from "@odoo_poll/js/poll_message";

// Extend Message component registry
patch(Message, {
    components: {
        ...Message.components,
        PollMessage,
    },
});

// Patch Message prototype lifecycle with getter
patch(Message.prototype, {
    get pollId() {
        const body = (this.message && this.message.body) || (this.props && this.props.message && this.props.message.body) || "";
        const match = body.match(/data-poll-id="(\d+)"/);
        return match ? parseInt(match[1]) : undefined;
    },
});
