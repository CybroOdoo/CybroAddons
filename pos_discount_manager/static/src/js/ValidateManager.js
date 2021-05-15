odoo.define('pos_discount_manager.ValidateManager', function(require) {
    'use strict';

    const {
        parse
    } = require('web.field_utils');
    const PosComponent = require('point_of_sale.PosComponent');
    const {
        useErrorHandlers
    } = require('point_of_sale.custom_hooks');
    const NumberBuffer = require('point_of_sale.NumberBuffer');
    const {
        useListener
    } = require('web.custom_hooks');
    const Registries = require('point_of_sale.Registries');
    const {
        onChangeOrder
    } = require('point_of_sale.custom_hooks');
    var PaymentScreen = require('point_of_sale.PaymentScreen')

    const ValidateManagers = (PaymentScreen) =>
        class extends PaymentScreen {

            constructor() {

                super(...arguments);

            }

            async _finalizeValidation() {
                if ((this.currentOrder.is_paid_with_cash() || this.currentOrder.get_change()) && this.env.pos.config.iface_cashdrawer) {
                    this.env.pos.proxy.printer.open_cashbox();
                }

                this.currentOrder.initialize_validation_date();
                this.currentOrder.finalized = true;

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

                var employee_dis = this.env.pos.get_cashier()['limited_discount'];
                var employee_name = this.env.pos.get_cashier()['name']

                var flag = 1;
                var global;

                var dis = 0;
                for (var i = 0; i < order.orderlines.length; i++) {
                    dis = dis + order.orderlines.models[i].discount;


                    if (order.orderlines.models[i].discount > employee_dis || order.orderlines.models[i].disc_percentage > employee_dis || dis > employee_dis) {
                        flag = 0;


                    }
                }
                if (flag != 1) {

                    const {
                        confirmed,
                        payload
                    } = await this.showPopup('NumberPopup', {
                        title: this.env._t(employee_name + ', your discount is over the limit. \n MANAGER pin for Approval'),
                    });

                    if (confirmed) {
                        var output = this.env.pos.employees.filter((obj) => obj.role == 'manager');
                        var pin = output[0].pin

                        if (Sha1.hash(payload) == pin) {

                        } else {
                            this.showPopup('ErrorPopup', {
                                title: this.env._t(" MANAGER RESTRICTED YOUR DISCOUNT"),
                                body: this.env._t(employee_name + ", Your Manager pin is INCORRECT."),

                            });
                            return false;

                        }
                    }

                }

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
                        // NOTE: Not yet sure if this should be awaited or not.
                        // If awaited, some operations like changing screen
                        // might not work.
                        this.env.pos.push_orders();

                    }
                }
            }
        };


    Registries.Component.extend(PaymentScreen, ValidateManagers);

    return ValidateManagers;

});