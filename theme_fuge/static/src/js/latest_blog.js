import { registry } from "@web/core/registry";
import { Component, useState, onWillStart} from "@odoo/owl";
import { rpc } from "@web/core/network/rpc";

export class FugeLatestBlog extends Component {
    static template = "theme_fuge.FugeLatestBlog";
    setup() {
        this.state = useState({ posts_recent: {}});
        onWillStart(async () => {
            this.state.posts_recent = await rpc("/get_blog_post", {});
        })
    }
}

registry.category("public_components").add("theme_fuge.FugeLatestBlog", FugeLatestBlog);
