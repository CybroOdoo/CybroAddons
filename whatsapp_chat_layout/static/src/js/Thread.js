import { Thread } from "@mail/core/common/thread_model";
import { patch } from "@web/core/utils/patch";

//Patching Thread Component
patch(Thread.prototype, {
    setup() {
        super.setup(...arguments);
    },
    async leave() {
        super.leave(...arguments);
        await location.reload();
    },
});
