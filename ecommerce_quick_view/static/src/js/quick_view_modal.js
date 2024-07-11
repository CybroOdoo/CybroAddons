/** @odoo-module **/

var core = require('web.core');
var rpc = require('web.rpc');
var publicWidget = require('web.public.widget');
require('website_sale.website_sale');

var QuickViewModal = publicWidget.Widget.extend({
    selector: '.oe_website_sale',
    events: {'click a.c-product-quick-view-action': '_onQuickViewClick',},
    init(params) {
        this._super(... arguments);
    },
    show_modal(template) {
        var $modal = $(template).appendTo($(this.selector));
        $modal.modal('show');
        core.bus.trigger('DOM_updated');
        // get the DOM element from the jQuery object
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
            var result = await rpc.query({
                route: '/c_quick_view/get_quick_view_html',
                params: {product_id: product_id},
            });
            self.show_modal(result);
        } catch (err) {
            reject(err);
        }
    },
});
publicWidget.registry.quick_view_modal = QuickViewModal;
return QuickViewModal;
