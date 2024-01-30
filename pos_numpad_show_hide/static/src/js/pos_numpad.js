///** @odoo-module **/

import { ProductScreen } from "@point_of_sale/app/screens/product_screen/product_screen";
import { patch } from "@web/core/utils/patch";


    patch(ProductScreen.prototype,  {
        NumpadVisibility() {
            //  hide  and show numPad in ProductScreen
            const padsElement = document.querySelector('.pads');
            const numpadToggleElement = document.querySelector('.numpad-toggle');
            const isNumpadVisible = padsElement.style.display !== 'none';
            padsElement.style.display = isNumpadVisible ? 'none' : 'block';
            numpadToggleElement.classList.remove('fa-eye', 'fa-eye-slash');
            numpadToggleElement.classList.add(isNumpadVisible ? 'fa-eye-slash' : 'fa-eye');
        }
    })

