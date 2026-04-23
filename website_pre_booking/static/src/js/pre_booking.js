/** @odoo-module **/
import publicWidget from '@web/legacy/js/public/public_widget';

publicWidget.registry.WebsiteSalePrebooking = publicWidget.Widget.extend({
    selector: '.pre_booking',
    events:{
        'click' : '_preBooking',
    },
    _preBooking: function (ev) {
        ev.preventDefault()
        let pre_max_qty = parseFloat($(ev.currentTarget).data('id'));
        const $quantityInput = $('input[name="add_qty"]');
        const add_qty_value = parseFloat($quantityInput.val());
        if (!isNaN(pre_max_qty) && !isNaN(add_qty_value)) {
            if (add_qty_value <= pre_max_qty) {
                window.location = $(ev.currentTarget).attr('data-url')+'?prod_qty='+add_qty_value
            } else {
                    window.location = '/sale/fail';
            }
        }
   }
});
