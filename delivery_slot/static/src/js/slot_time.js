/** @odoo-module */
import publicWidget from '@web/legacy/js/public/public_widget';
import { jsonrpc } from "@web/core/network/rpc_service";
    /**
     * Widget that handles the slot time selection on the cart line.
     */
    publicWidget.registry.websiteSlotTimeHours = publicWidget.Widget.extend({
        selector: '.slot-time-div',
        events: {
            'change input[type="radio"][name="slot_hour"]': '_onSlotTime',
        },
        _onSlotTime: function(ev) {
            var selected_option = $("input[type='radio'][name='slot_hour']:checked").val()
            jsonrpc('/shop/cart/get_option',{
                    'selected_option': selected_option,
                })
                .then(function(result) {
                    const selects = document.querySelectorAll('select');
                    const input = document.querySelector('input');
                    selects.forEach((select) => {
                        const options = Array.from(select.options);
                        options.forEach((option) => {
                            option.remove();
                        });
                        result.forEach((item) => {
                            let newOption = new Option(item[1], item[0]);
                            select.add(newOption, undefined);
                        });
                    });
                });
        },
    });
