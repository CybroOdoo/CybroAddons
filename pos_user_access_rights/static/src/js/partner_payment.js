odoo.define('pos_user_access_rights.partner_payment', function (require) {
"use strict";
const Registries = require('point_of_sale.Registries');
const PaymentScreen = require('point_of_sale.PaymentScreen');

const partner = (PaymentScreen) =>
  class extends PaymentScreen {
    async selectPartner() {
  let disableButton = false;
    const disablePaymentCustomer =  this.env.pos.res_users.disable_customer_selection;  // access disable customer selection field from res users
    if (disablePaymentCustomer) {
      disableButton = true;
    }
  if (disableButton) {
    const buttonEl = document.querySelector(".partner-button .button");          // select customer selection button using class name
    if (buttonEl) {
      buttonEl.classList.add("disabled");                                   // add class disabled to disable the button
      buttonEl.style.cursor = "not-allowed";                                // add style to the button to disallow the cursor
      buttonEl.style.backgroundColor = '#C9CCD2';                           // add style to the button to provide background color
    }
  } else {
    return super.selectPartner();
    }
  }
  }
Registries.Component.extend(PaymentScreen, partner);
});