/** @odoo-module **/
import { patch } from "@web/core/utils/patch";
import { DiscussSidebar } from "@mail/core/web/discuss_sidebar";
import { DiscussSidebarCategories } from "@mail/discuss/core/web/discuss_sidebar_categories";

patch(DiscussSidebarCategories.prototype, {
    setup() {
             super.setup();
             },
    openThread(ev, thread) {
        this.env.bus.trigger("HIDE:CHAT")
        this.threadService.setDiscussThread(thread);
    },
});

DiscussSidebarCategories.props = {
    ...DiscussSidebarCategories.props,
    sidebar: {type: String, optional: true},
}
