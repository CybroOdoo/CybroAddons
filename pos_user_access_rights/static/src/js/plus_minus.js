odoo.define('pos_user_access_rights.plus_minus', function (require) {
"use strict";
const Registries = require('point_of_sale.Registries');
const NumpadWidget = require('point_of_sale.NumpadWidget');


 const button = (NumpadWidget) =>
  class extends NumpadWidget {
   sendInput(key) {
    let disableButton = false;
        const disable_Plus_Minus_Button = this.env.pos.res_users.disable_plus_minus_button;  // access disable plus minus button field from res users
        if (disable_Plus_Minus_Button && key === '-') {                    // it only select the plus minus key
            disableButton = true;
        }
    if (disableButton) {
        const buttonEl = document.querySelector(".numpad-minus");         // select the numpad plus minus button using class name
        if (buttonEl) {
            buttonEl.disabled = true;
            buttonEl.classList.add('disabled');                           // add class disabled to disable the button
            buttonEl.style.cursor = "not-allowed";                        // add style to the button to disallow the cursor
            buttonEl.style.backgroundColor = '#C9CCD2';                   // add style to the button to provide background color
        }
    } else {
        super.sendInput(key);
    }
}

    }
    Registries.Component.extend(NumpadWidget, button);
    return button

});