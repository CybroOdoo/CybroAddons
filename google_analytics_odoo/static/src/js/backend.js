/** @odoo-module **/
import { FormController } from "@web/views/form/form_controller";
import { patch } from "@web/core/utils/patch";
const ajax = require('web.ajax');

//Patch the FormController to Send the Events to Google Analytics
//From the Backed
patch(FormController.prototype, "FormController.google", {
    //Super the setup Function
    setup() {
        this._super.apply(this, arguments);
    },
    //Override the afterExecuteActionButton function to send the evens
    async afterExecuteActionButton(clickParams) {
        var self = this;
        await ajax.jsonRpc("/analytics", 'call', {}).then(function(data) {
            self.measurement_id = data.measurement_id
            self.api_secret = data.api_secret
            self.enable_analytics=data.enable_analytics
        });
        self.measurement_id = this.measurement_id;
        self.api_secret = this.api_secret;
        self.enable_analytics = this.enable_analytics
        if (self.enable_analytics)
         {
            if (self.measurement_id != false && self.api_secret != false) {
                if (clickParams.name === "action_confirm" && this.props.resModel === "sale.order") {
                    var order_id = this.model.root.data.id
                    var self = this
                    ajax.jsonRpc("/sale_analytics", 'call', {'order_id':order_id}).then(function(data) {
                        gtag('get', self.measurement_id, 'client_id', (clientID) => {
                            sendSaleEvent(clientID, "Sales", data['sales_data'])
                        });
                         // Sending the event to Google Analytics when confirming
                         // Sale order.
                        function sendSaleEvent(clientID, eventName, eventData) {
                            fetch(`https://www.google-analytics.com/mp/collect?measurement_id=${self.measurement_id}&api_secret=${self.api_secret}`, {
                                method: "POST",
                                body: JSON.stringify({
                                    client_id: clientID,
                                    events: [{
                                        name: 'Sales_Order',
                                        params: {
                                            "Number": String(eventData.name),
                                            "Customer": String(eventData.customer),
                                            "Amount": String(eventData.amount),
                                        }
                                    }]
                                })
                            });
                        }
                    });
                }
                if (clickParams.name === "button_confirm" && this.props.resModel === "purchase.order") {
                    var order_id = this.model.root.data.id
                    var self = this
                    ajax.jsonRpc("/purchase_analytics", 'call', {'order_id':order_id}).then(function(data) {
                        gtag('get', self.measurement_id, 'client_id', (clientID) => {
                            sendPurchaseEvent(clientID, "Purchase", data['purchase_data'])
                        });
                        function sendPurchaseEvent(clientID, eventName, eventData) {
                         // Sending the event to Google Analytics when confirming
                         // Purchase order.
                            fetch(`https://www.google-analytics.com/mp/collect?measurement_id=${self.measurement_id}&api_secret=${self.api_secret}`, {
                                method: "POST",
                                body: JSON.stringify({
                                    client_id: clientID,
                                    events: [{
                                        name: 'purchase_order',
                                        params: {
                                            "Number": String(eventData.name),
                                            "Customer": String(eventData.customer),
                                            "Amount": String(eventData.amount),
                                        }
                                    }]
                                })
                            });
                        }
                    });
                }
                if (clickParams.name === "action_post" && this.props.resModel === "account.move") {
                    var order_id = this.model.root.data.id
                        ajax.jsonRpc("/invoice_analytics", 'call', {'order_id':order_id}).then(function(data) {
                        gtag('get', self.measurement_id, 'client_id', (clientID) => {
                            sendInvoiceEvent(clientID, "addoAFF", data['invoice_data'])
                        });
                         // Sending the event to Google Analytics when confirming
                         // Invoice.
                        function sendInvoiceEvent(clientID, eventName, eventData) {
                            fetch(`https://www.google-analytics.com/mp/collect?measurement_id=${self.measurement_id}&api_secret=${self.api_secret}`, {
                                method: "POST",
                                body: JSON.stringify({
                                    client_id: clientID,
                                    events: [{
                                        name: 'Invoices',
                                        params: {
                                            "Number": String(eventData.name),
                                            "Customer": String(eventData.customer),
                                            "Amount": String(eventData.amount),
                                        }
                                    }]
                                })
                            });
                        }
                    });
                }
                if (clickParams.special !== "cancel") {
                    return this.model.root
                        .save({
                            stayInEdition: true,
                            useSaveErrorDialog: !this.env.inDialog
                        })
                        .then((saved) => {
                            if (saved && this.props.onSave) {
                                this.props.onSave(this.model.root);
                            }
                            return saved;
                        });
                } else if (this.props.onDiscard) {
                    this.props.onDiscard(this.model.root);
                }
            }
         }
    }
});
