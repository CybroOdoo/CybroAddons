odoo.define('pos_user_access_rights.numpad_keys', function (require) {
"use strict";
const Registries = require('point_of_sale.Registries');
const NumpadWidget = require('point_of_sale.NumpadWidget');
 const numpad = (NumpadWidget) =>
  class extends NumpadWidget {

sendInput(key) {
    let disableButton = false;
        const disableNumpad = this.env.pos.res_users.disable_numpad;                // access the disable numpad field from res users
        if (disableNumpad && key !== 'Backspace' && key !== '-') {
            disableButton = true;
        }
    if (disableButton) {
        const buttonEls = document.querySelectorAll(".number-char");  // select the numbers in numpad  using class name
        buttonEls.forEach((buttonEl) => {
            if (buttonEl.innerText !== 'Backspace' && buttonEl.innerText !== '-') {   // condition to select only the numbers in numpad
                buttonEl.disabled = true;
                buttonEl.classList.add('disabled');     // add class disabled to disable the button
                buttonEl.style.cursor = "not-allowed";     // add style to the button to disallow the cursor
                buttonEl.style.backgroundColor = '#C9CCD2'; // add style to the button to provide background color
            }
        });
    } else {
        super.sendInput(key);
    }
}
 }
    Registries.Component.extend(NumpadWidget, numpad);
    return numpad

});