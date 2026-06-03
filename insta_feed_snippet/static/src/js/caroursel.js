/** @odoo-module **/

import publicWidget from "@web/legacy/js/public/public_widget";
import { jsonrpc } from "@web/core/network/rpc_service";

publicWidget.registry.get_dashboard_carousel = publicWidget.Widget.extend({
    selector: '.s_carousel_template',
    start: function () {
        var self = this;
        return jsonrpc('/get_dashboard_carousel', {}).then(function (data) {
            if (data && data.trim().length > 0) {
                self.$target.empty().append(data);
            } else {
                console.warn("Instagram Feed Snippet: No data returned from server. Showing placeholder.");
                self.$target.html(`
                    <div class="container py-5">
                        <div class="alert alert-warning text-center shadow-sm">
                            <i class="fa fa-exclamation-triangle fa-3x mb-3 text-warning"></i>
                            <h3>No Instagram Posts Found</h3>
                            <p class="lead">The snippet is active, but there are no posts to display.</p>
                            <hr/>
                            <p>To show your feed, please go to the <b>Odoo Backend > Website > Instagram Post</b> and ensure you have records with images.</p>
                        </div>
                    </div>
                `);
            }
        });
    },
});
