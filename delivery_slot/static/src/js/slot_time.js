/** @odoo-module */
import publicWidget from '@web/legacy/js/public/public_widget';
import { rpc } from "@web/core/network/rpc";

publicWidget.registry.websiteSlotTimeHours = publicWidget.Widget.extend({
    selector: '.slot-time-div',
    events: {
        'change input[type="radio"][name="slot_hour"]': '_onSlotTime',
    },
    /**
     * Event handler for slot hour radio button selection.
     *
     * When a user selects a different slot hour, this function refreshes each
     * delivery slot <select> (#slot_id). If a delivery date is selected, only
     * available slots for that date and slot type are shown.
     *
     * @param {Event} ev - The change event triggered by selecting a radio button.
     */
    _onSlotTime: function (ev) {
        var selected_option = $("input[type='radio'][name='slot_hour']:checked").val();
        const deliverySlotDivs = document.querySelectorAll('.delivery_slot_div');

        deliverySlotDivs.forEach(function (deliverySlotDiv) {
            const deliveryDate = deliverySlotDiv.querySelector('#date');
            const deliverySelect = deliverySlotDiv.querySelector('#slot_id');
            const route = deliveryDate && deliveryDate.value
                ? '/shop/cart/get_available_slots'
                : '/shop/cart/get_option';
            const params = {'selected_option': selected_option};

            if (!deliverySelect) {
                return;
            }
            if (deliveryDate && deliveryDate.value) {
                params.date = deliveryDate.value;
            }

            rpc(route, params).then(function (result) {
                deliverySelect.innerHTML = '';
                deliverySelect.add(new Option('Select a slot', ''));
                result.forEach((item) => {
                    deliverySelect.add(new Option(item[1], item[0]));
                });
                deliverySelect.selectedIndex = 0;
            });
        });
    },
});
