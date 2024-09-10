/** @odoo-module */
// Import dependencies
import { patch } from "@web/core/utils/patch";
import { ReceiptScreen } from "@point_of_sale/app/screens/receipt_screen/receipt_screen";
import { jsonrpc } from "@web/core/network/rpc_service";
import { _t } from "@web/core/l10n/translation";
/**
 * Patch ReceiptScreen to include functions for sending invoices and receipts via WhatsApp.
 */
patch(ReceiptScreen.prototype, {
    setup() {
        super.setup();
    },
    //Function for sending Invoices via Whatsapp
    sendInvoiceOnWhatsapp() {
        this.orderUiState.whatsappInvoiceSuccessful = null
        this.orderUiState.isInvoiceSending = true;
        var self = this;
        const order_id = this.currentOrder.server_id
        jsonrpc('/web/dataset/call_kw/pos.order/action_send_invoice', {
            model: 'pos.order',
            method: 'action_send_invoice',
            args: [0],
            kwargs: {
                order_id: order_id,
                number: this.currentOrder.get_partner().whatsapp_number,
                config_id: this.pos.config.id
            }
        }).then(function(result) {
            if (!result) {
                self.orderUiState.isInvoiceSending = false;
                self.orderUiState.whatsappInvoiceSuccessful = true;
                self.orderUiState.whatsappInvoiceNotice = _t("Message sent to Whatsapp.");
            } else {
                self.orderUiState.isInvoiceSending = false;
                self.orderUiState.whatsappInvoiceSuccessful = false;
                self.orderUiState.whatsappInvoiceNotice = _t("Wrong inputs detected. This may be due to incorrect API data entry or selecting the wrong session or whatsapp number is not given.");
            }
        });
    },
    //Function for sending Receipts via Whatsapp
    sendReceiptOnWhatsapp() {
        this.orderUiState.whatsappReceiptSuccessful = null
        this.orderUiState.isReceiptSending = true;
        setTimeout(async () => {
            try {
                try {
                    const res = await jsonrpc('/web/dataset/call_kw/pos.order/get_instance', {
                        model: 'pos.order',
                        method: 'get_instance',
                        args: [0],
                        kwargs: {config_id: this.pos.config.id}
                    });
                    if (res.instant_id) {
                        if (this.currentOrder.get_partner().whatsapp_number) {
                            await this._sendWhatsappReceiptToCustomer();
                            this.orderUiState.isReceiptSending =false;
                            this.orderUiState.whatsappReceiptSuccessful = true;
                            this.orderUiState.whatsappReceiptNotice = _t("Message sent to Whatsapp.");
                        }
                        else{
                            this.orderUiState.isReceiptSending = false;
                            this.orderUiState.whatsappReceiptSuccessful = false;
                            this.orderUiState.whatsappReceiptNotice = _t("Wrong inputs detected. This may be due to whatsapp number is not given.");
                        }
                    } else {
                        this.orderUiState.isReceiptSending = false;
                        this.orderUiState.whatsappReceiptSuccessful = false;
                        this.orderUiState.whatsappReceiptNotice = _t("Wrong inputs detected. This may be due to incorrect API data entry or selecting the wrong session.");
                    }
                } catch (error) {
                    console.error("Authentication Error:", error);
                }
            } catch {
                this.orderUiState.isReceiptSending = false;
                this.orderUiState.whatsappReceiptSuccessful = false;
                this.orderUiState.whatsappReceiptNotice = _t("Sending message failed. Please try again.");
            }
        }, 1000);
    },
    async _sendWhatsappReceiptToCustomer() {
        var self = this;
        const partner = this.currentOrder.get_partner();
        const orderPartner = {
            name: partner.name,
            whatsapp: partner.whatsapp_number,
            config_id: this.pos.config.id
        };
        const configId = this.pos.config.id;
        const result = await this.sendToCustomer(orderPartner, "action_send_receipt");
    },
});
