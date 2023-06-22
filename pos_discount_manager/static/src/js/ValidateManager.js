odoo.define('pos_discount_manager.ValidateManager', function(require) {
    'use strict';

  const Registries = require('point_of_sale.Registries');
  const PaymentScreen = require('point_of_sale.PaymentScreen');

     const ValidateManagers = (PaymentScreen) =>
        class extends PaymentScreen {
                /**
                *Override the validate button to approve discount limit
                */
            async _finalizeValidation() {
             if ((this.currentOrder.is_paid_with_cash() || this.currentOrder.get_change()) && this.env.pos.config.iface_cashdrawer) {
                    this.env.pos.proxy.printer.open_cashbox();
             }

                this.currentOrder.initialize_validation_date();
                let syncedOrderBackendIds = [];
                try {
                    if (this.currentOrder.is_to_invoice()) {
                        syncedOrderBackendIds = await this.env.pos.push_and_invoice_order(
                            this.currentOrder
                        );
                    } else {
                        syncedOrderBackendIds = await this.env.pos.push_single_order(this.currentOrder);
                    }
                } catch (error) {
                    if (error instanceof Error) {
                        throw error;
                    } else {
                        await this._handlePushOrderError(error);
                    }
                }
                if (syncedOrderBackendIds.length && this.currentOrder.wait_for_push_order()) {
                    const result = await this._postPushOrderResolve(
                        this.currentOrder,
                        syncedOrderBackendIds
                    );
                    if (!result) {
                        await this.showPopup('ErrorPopup', {
                            title: 'Error: no internet connection.',
                            body: error,
                        });
                    }
                }

            var order = this.env.pos.get_order();
            var orderlines = this.currentOrder.get_orderlines()
            var employee_dis = this.env.pos.get_cashier()['limited_discount'];
            var employee_name = this.env.pos.get_cashier()['name']
            var flag = 1;
             orderlines.forEach((order) => {
               if(order.discount > employee_dis)
               flag = 0;
             });
             if (flag != 1) {
             const {confirmed,payload} = await this.showPopup('NumberPopup', {
                        title: this.env._t(employee_name + ', your discount is over the limit. \n Manager pin for Approval'),
                    });
                    if(confirmed){
                     var output = this.env.pos.employees.filter((obj) => obj.role == 'manager');
                     var pin = output[0].pin
                     if (Sha1.hash(payload) == pin) {
                        this.showScreen(this.nextScreen);
                        }
                        else {
                            this.showPopup('ErrorPopup', {
                                title: this.env._t(" Manager Restricted your discount"),
                                body: this.env._t(employee_name + ", Your Manager pin is incorrect."),

                            });
                            return false;
                        }
                    }
                    else {
                        return false;
                    }
                    }
                    this.currentOrder.finalized = true;
                    this.showScreen(this.nextScreen);
                    // If we succeeded in syncing the current order, and
                   // there are still other orders that are left unsynced,
                  // we ask the user if he is willing to wait and sync them.
                  if (syncedOrderBackendIds.length && this.env.pos.db.get_orders().length) {
                    const {
                        confirmed
                    } = await this.showPopup('ConfirmPopup', {
                        title: this.env._t('Remaining unsynced orders'),
                        body: this.env._t(
                            'There are unsynced orders. Do you want to sync these orders?'
                        ),
                    });
                     if (confirmed) {
                     // Not yet sure if this should be awaited or not.
                        this.env.pos.push_orders();
                     }
                  }
             }
        }
     Registries.Component.extend(PaymentScreen, ValidateManagers);
     return ValidateManagers;
});