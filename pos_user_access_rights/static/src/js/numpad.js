odoo.define('pos_user_access_rights.numpad', function (require) {
"use strict";
const Registries = require('point_of_sale.Registries');
const NumpadWidget = require('point_of_sale.NumpadWidget');
 const numpad = (NumpadWidget) =>
  class extends NumpadWidget {
 get hasPriceControlRights() {
 let disableButton = false;
    const disablePriceButton = this.env.pos.res_users.disable_price_button; // access the value of disable price button field from res users
    if (disablePriceButton) {
      disableButton = true;
    }
  if (disableButton) {
    const buttonEl = document.querySelector(".price");     // select the price button using selector
    if (buttonEl) {
     buttonEl.disabled = true;
       buttonEl.classList.add('disabled');                // add class disabled to disable the button when the field is enabled
    }
  } else {
  return super.hasPriceControlRights;
  }
 }


 get hasManualDiscount() {
 let disableButton = false;
    const disableDiscountButton = this.env.pos.res_users.disable_discount_button; // access the disable discount button field from res users
    if (disableDiscountButton) {
      disableButton = true;
    }
  if (disableButton) {
    const buttonEl = document.querySelector(".discount");        // select the discount button using selector
    if (buttonEl) {
     buttonEl.disabled = true;
       buttonEl.classList.add('disabled');                       // add class disabled to disable the button when the field is enabled
    }
  } else {
  return super.hasManualDiscount;
  }
 }

 sendInput(key) {
    let disableButton = false;
        const disableNumpad =  this.env.pos.res_users.disable_remove_button; // access the disable remove button field from res users
        if (disableNumpad && key === 'Backspace') {      // it only check the backspace key
            disableButton = true;
        }
    if (disableButton) {
        const buttonEl = document.querySelector(".numpad-backspace"); // select the backspace button using the selector
        if (buttonEl) {
            buttonEl.disabled = true;
            buttonEl.classList.add('disabled');                      // add class disabled to disable the button when the field is enabled
            buttonEl.style.cursor = "not-allowed";                   // add style to the button to disallow the cursor
            buttonEl.style.backgroundColor = '#C9CCD2';              // add style to the button to provide background color
        }
    } else {
        super.sendInput(key);
    }
}
  }
    Registries.Component.extend(NumpadWidget, numpad);
    return numpad

});

