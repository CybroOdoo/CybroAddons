/** @odoo-module **/
import {WebsiteSale} from "@website_sale/js/website_sale";
import publicWidget from '@web/legacy/js/public/public_widget';

publicWidget.registry.WebsiteSalePrebooking = publicWidget.Widget.extend({
    selector: '#product_detail',
    events:{
        'click .pre_booking': '_preBooking',
    },
    _preBooking: function (ev) {
        let pre_max_qty = parseFloat($(ev.currentTarget).data('id'));
        let add_qty_value = parseFloat($('.quantity').val());
        if (!isNaN(pre_max_qty) && !isNaN(add_qty_value)) {
            if (pre_max_qty >= add_qty_value) {
                window.location = $(ev.currentTarget).val()+'?prod_qty='+add_qty_value
            } else {
                    window.location = '/sale/fail';
            }
        }
   }
});
