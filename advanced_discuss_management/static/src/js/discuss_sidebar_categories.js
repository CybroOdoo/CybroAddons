/** @odoo-module **/
import { DiscussSidebarCategories } from "@mail/discuss/core/public_web/discuss_sidebar_categories";

DiscussSidebarCategories.props = {
    ...DiscussSidebarCategories.props,
    sidebar: {
        type: String,
        optional: true,
    },
};
