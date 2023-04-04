odoo.define('pos_user_access_rights.product_screen_buttons', function (require) {
"use strict";
var {PosGlobalState,OrderLIne} = require('point_of_sale.models');
const Registries = require('point_of_sale.Registries');
const ProductScreen = require('point_of_sale.ProductScreen');
const NewPosGlobalState = (PosGlobalState) => class NewPosGlobalState extends PosGlobalState {

     async _processData(loadedData){
        await super._processData(...arguments);
        this.res_users = loadedData['res.users'];
    }
}
Registries.Model.extend(PosGlobalState,NewPosGlobalState)


 const pay = (ProductScreen) =>
  class extends ProductScreen {
    async _onClickPay() {
  let disableButton = false;
    const disablePaymentSelection = this.env.pos.res_users.disable_payment_button;  // access the disable payment selection field from res users
    if (disablePaymentSelection) {
      disableButton = true;
    }
  if (disableButton) {
    const buttonEl = document.querySelector(".button.pay.validation");  // select the payment button using class name
    console.log(buttonEl)
    if (buttonEl) {
       buttonEl.classList.add('disabled');                             // add class disabled to disable the button
       buttonEl.style.cursor = "not-allowed";                           // add style to the button to disallow the cursor
       buttonEl.style.backgroundColor = '#C9CCD2';                       // add style to the button to provide background color

    }
  } else {
    return super._onClickPay();
  }
}

async onClickPartner() {
  let disableButton = false;
    const disableCustomerSelection = this.env.pos.res_users.disable_customer_selection;  // access disable customer selection field from res users
    if (disableCustomerSelection) {
      disableButton = true;
    }
  if (disableButton) {
    const buttonEl = document.querySelector(".button.set-partner");          // select customer selection button using class name
    if (buttonEl) {
      buttonEl.classList.add("disabled");                                   // add class disabled to disable the button
      buttonEl.style.cursor = "not-allowed";                                // add style to the button to disallow the cursor
      buttonEl.style.backgroundColor = '#C9CCD2';                           // add style to the button to provide background color
    }
  } else {
    return super.onClickPartner();
  }
}

}
      Registries.Component.extend(ProductScreen, pay);

});