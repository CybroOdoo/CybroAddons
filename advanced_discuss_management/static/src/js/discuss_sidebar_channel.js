/** @odoo-module **/
import { patch } from "@web/core/utils/patch";
import { DiscussSidebarChannel } from "@mail/discuss/core/public_web/discuss_sidebar_categories";
import { markEventHandled } from "@web/core/utils/misc";

patch(DiscussSidebarChannel.prototype, {
    setup() {
        super.setup();
    },
    openThread(ev, thread) {
        // to trigger the event to hide custom div areas
        this.env.bus.trigger("HIDE:CHAT")
        markEventHandled(ev, "sidebar.openThread");
        thread.setAsDiscussThread();
    },
});
