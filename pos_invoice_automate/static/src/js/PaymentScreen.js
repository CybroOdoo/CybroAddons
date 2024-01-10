odoo.define('pos_invoice_automate.PaymentScreen', function(require) {
    'use strict';
    const PaymentScreen = require('point_of_sale.PaymentScreen');
    const Registries = require('point_of_sale.Registries');
    var rpc = require('web.rpc');
    const {
        useErrorHandlers,
        useAsyncLockedMethod
    } = require('point_of_sale.custom_hooks');
    const PosInvoiceAutomatePaymentScreen = (PaymentScreen) =>
        class extends PaymentScreen {
            constructor() {
                super(...arguments);
                if (this.env.pos.config.invoice_auto_check) {
                    this.currentOrder.set_to_invoice(true);
                }
            }
            async validateOrder(isForceValidate) {
                const value = await this.env.pos.push_single_order(this.currentOrder);
                const config_id = this.env.pos.config.id
                const order_id = value[0].id
                if (this.env.pos.config.is_started) {
                    await this.rpc({
                        model: 'pos.config',
                        method: 'start_cron',
                        args: [config_id],
                    });
                } else {
                    if (this.env.pos.config.button_operation == 'download') {
                        var self = this;
                        await this.rpc({
                            model: 'pos.order',
                            method: 'download_invoice',
                            args: [order_id],
                        }).then(function(result) {
                            self.env.legacyActionManager.do_action(result)
                        })
                    } else if (this.env.pos.config.button_operation == 'send') {
                        await this.rpc({
                            model: 'pos.order',
                            method: 'send_mail_invoice',
                            args: [order_id],
                        });
                    } else if (this.env.pos.config.button_operation == 'download_send_mail') {
                        var self = this;
                        await this.rpc({
                            model: 'pos.order',
                            method: 'send_mail_invoice',
                            args: [order_id],
                        }).then(function(result) {
                            self.env.legacyActionManager.do_action(result)
                        })
                    }
                }
                await super.validateOrder(isForceValidate);
            }
            async _finalizeValidation() {
                if ((this.currentOrder.is_paid_with_cash() || this.currentOrder.get_change()) && this.env.pos.config.iface_cashdrawer && this.env.proxy && this.env.proxy.printer) {
                    this.env.proxy.printer.open_cashbox();
                }
                this.currentOrder.initialize_validation_date();
                for (let line of this.paymentLines) {
                    if (!line.amount === 0) {
                        this.currentOrder.remove_paymentline(line);
                    }
                }
                this.currentOrder.finalized = true;
                let syncOrderResult, hasError;
                try {
                    // 1. Save order to server.
                    syncOrderResult = await this.env.pos.push_single_order(this.currentOrder);
                    // 2. Invoice.
                    if (this.shouldDownloadInvoice() && this.currentOrder.is_to_invoice()) {
                        if (syncOrderResult.length) {
                            await this.env.legacyActionManager.do_action('account.account_invoices', {
                                additional_context: {
                                    active_ids: [syncOrderResult[0].account_move],
                                },
                            });
                        } else {
                            throw {
                                code: 401,
                                message: 'Backend Invoice',
                                data: {
                                    order: this.currentOrder
                                }
                            };
                        }
                    }
                    // 3. Post process.
                    if (syncOrderResult.length && this.currentOrder.wait_for_push_order()) {
                        const postPushResult = await this._postPushOrderResolve(
                            this.currentOrder,
                            syncOrderResult.map((res) => res.id)
                        );
                        if (!postPushResult) {
                            this.showPopup('ErrorPopup', {
                                title: this.env._t('Error: no internet connection.'),
                                body: this.env._t('Some, if not all, post-processing after syncing order failed.'),
                            });
                        }
                    }
                } catch (error) {
                    if (error.code == 700 || error.code == 701)
                        this.error = true;

                    if ('code' in error) {
                        // We started putting `code` in the rejected object for invoicing error.
                        // We can continue with that convention such that when the error has `code`,
                        // then it is an error when invoicing. Besides, _handlePushOrderError was
                        // introduce to handle invoicing error logic.
                        if (this.env.pos.config.button_operation == 'send') {
                            await this._handlePushOrderError(error);
                        }
                    } else {
                        // We don't block for connection error. But we rethrow for any other errors.
                        if (isConnectionError(error)) {
                            this.showPopup('OfflineErrorPopup', {
                                title: this.env._t('Connection Error'),
                                body: this.env._t('Order is not synced. Check your internet connection'),
                            });
                        } else {
                            throw error;
                        }
                    }
                } finally {
                    // Always show the next screen regardless of error since pos has to
                    // continue working even offline.
                    this.showScreen(this.nextScreen);
                    // Remove the order from the local storage so that when we refresh the page, the order
                    // won't be there
                    this.env.pos.db.remove_unpaid_order(this.currentOrder);

                    // Ask the user to sync the remaining unsynced orders.
                    if (!hasError && syncOrderResult && this.env.pos.db.get_orders().length) {
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
            }
        };
    Registries.Component.extend(PaymentScreen, PosInvoiceAutomatePaymentScreen);
    return PaymentScreen;
});
