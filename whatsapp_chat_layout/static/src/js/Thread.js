import { Thread } from "@mail/core/common/thread_model";
import { patch } from "@web/core/utils/patch";

patch(Thread.prototype, {
    async leave() {
        await super.leave(...arguments);
        location.reload();
    },
});
