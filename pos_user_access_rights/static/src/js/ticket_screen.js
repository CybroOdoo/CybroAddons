odoo.define('pos_user_access_rights.ticket_screen', function (require) {
"use strict";
const Registries = require('point_of_sale.Registries');
const TicketScreen = require('point_of_sale.TicketScreen');
const { onMounted } = owl;


const order = (TicketScreen) =>
  class extends TicketScreen {
  onMounted() {
  let hideButtons = false;
    const disableNewOrders = this.env.pos.res_users.hide_new_orders;       //access hide new orders field from res users
    if (disableNewOrders) {
      hideButtons = true;
    }

  const newOrderButtonEl = document.querySelector(".buttons button.highlight");   // select new order button using class name
  if (hideButtons && newOrderButtonEl) {
      newOrderButtonEl.style.display = "none";  // hide the button using display style
  }


 const deleteOrderButtonEls = document.querySelectorAll(".delete-button");   // select delete order button using class name
        if (deleteOrderButtonEls.length > 0) {
          let hideButtons = false;
          if (this.env.pos.res_users.hide_delete_button) {
              hideButtons = true;
            }
          if (hideButtons) {
            deleteOrderButtonEls.forEach((deleteOrderButtonEls) => {
              deleteOrderButtonEls.style.display = "none";             // hide the button using display style
            });
            }
            }
    }
    }
    Registries.Component.extend(TicketScreen, order);

});