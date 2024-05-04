/** @odoo-module **/
import publicWidget from "@web/legacy/js/public/public_widget";
import { jsonrpc } from "@web/core/network/rpc_service";

publicWidget.registry.QuickViewModal = publicWidget.Widget.extend({
    selector: '.oe_website_sale',
    events: {'click a.c-product-quick-view-action': '_onQuickViewClick',},
    init(params) {
        this._super(... arguments);
    },
    show_modal(template) {
        var $modal = $(template).appendTo($(this.selector));
        $modal.modal('show');
        // attach an event listener to remove the modal from the DOM when it is hidden
        $modal.get(0).addEventListener('hidden.bs.modal', function (event) {
            $modal.remove();
        }, {once: true});
    },
    async _onQuickViewClick(ev) {
        ev.preventDefault();
        var product_id = $(ev.currentTarget).data('product-id');
        var self = this;
        try {
            var result = await jsonrpc('/c_quick_view/get_quick_view_html', {product_id: product_id});
            self.show_modal(result);
        } catch (err) {
            alert(err);
        }
    },
});
export default publicWidget.registry.QuickViewModal;
