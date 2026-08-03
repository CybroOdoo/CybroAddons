/** @odoo-module */
// Import dependencies
import { patch } from "@web/core/utils/patch";
import { ReceiptScreen } from "@point_of_sale/app/screens/receipt_screen/receipt_screen";
import { rpc } from "@web/core/network/rpc";
import { _t } from "@web/core/l10n/translation";
import { useState } from "@odoo/owl";
/**
 * Patch ReceiptScreen to include functions for sending invoices and receipts via WhatsApp.
 */
patch(ReceiptScreen.prototype, {
    setup() {
        super.setup();
        this.orderUiState = useState({
            whatsappInvoiceSuccessful: null,
            isInvoiceSending: false,
            whatsappInvoiceNotice: "",
            whatsappReceiptSuccessful: null,
            isReceiptSending: false,
            whatsappReceiptNotice: "",
        });
    },
    //Function for sending Invoices via Whatsapp
    sendInvoiceOnWhatsapp() {
        this.orderUiState.whatsappInvoiceSuccessful = null
        this.orderUiState.isInvoiceSending = true;
        var self = this;
        const order_id = this.currentOrder.id
        rpc('/web/dataset/call_kw/pos.order/action_send_invoice', {
            model: 'pos.order',
            method: 'action_send_invoice',
            args: [0],
            kwargs: {
                order_id: order_id,
                number: this.currentOrder.getPartner()?.whatsapp_number,
                config_id: this.pos.config.id
            }
        }).then(function(result) {
            if (!result) {
                self.orderUiState.isInvoiceSending = false;
                self.orderUiState.whatsappInvoiceSuccessful = true;
                self.orderUiState.whatsappInvoiceNotice = _t("Invoice sent to Whatsapp.");
            } else {
                self.orderUiState.isInvoiceSending = false;
                self.orderUiState.whatsappInvoiceSuccessful = false;
                self.orderUiState.whatsappInvoiceNotice = _t("Wrong inputs detected. This may be due to incorrect API data entry or selecting the wrong session or whatsapp number is not given.");
            }
        });
    },
    sendReceiptOnWhatsapp() {
        this.orderUiState.whatsappReceiptSuccessful = null
        this.orderUiState.isReceiptSending = true;
        setTimeout(async () => {
            try {
                const res = await rpc('/web/dataset/call_kw/pos.order/get_instance', {
                    model: 'pos.order',
                    method: 'get_instance',
                    args: [0],
                    kwargs: {config_id: this.pos.config.id}
                });
                if (res.instant_id) {
                    if (this.currentOrder.getPartner()?.whatsapp_number) {
                        await this._sendWhatsappReceiptToCustomer();
                        this.orderUiState.isReceiptSending = false;
                        this.orderUiState.whatsappReceiptSuccessful = true;
                        this.orderUiState.whatsappReceiptNotice = _t("Receipt sent to Whatsapp.");
                    }
                    else {
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
                console.error("WhatsApp Send Error:", error);
                this.orderUiState.isReceiptSending = false;
                this.orderUiState.whatsappReceiptSuccessful = false;
                this.orderUiState.whatsappReceiptNotice = _t("Sending message failed. Please try again.");
            }
        }, 1000);
    },
    async _sendWhatsappReceiptToCustomer() {
        const order = this.currentOrder;
        const partner = order.getPartner();
        const ticketImage = await this.generateTicketImage();
        const orderPartner = {
            name: partner.name,
            whatsapp: partner.whatsapp_number,
            config_id: this.pos.config.id,
        };
        await this.pos.data.call("pos.order", "action_send_receipt", [
            [order.id],
            order.name,
            orderPartner,
            ticketImage,
        ]);
    },
});
