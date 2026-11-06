/** @odoo-module */
import { patch } from "@web/core/utils/patch";
import { FeedbackScreen } from "@point_of_sale/app/screens/feedback_screen/feedback_screen";
import { _t } from "@web/core/l10n/translation";
import { signal } from "@odoo/owl";

/**
 * Patch FeedbackScreen to support WhatsApp receipt and invoice actions.
 */
patch(FeedbackScreen.prototype, {
    setup() {
        super.setup(...arguments);
        this.isSendingReceipt = signal(false);
        this.isSendingInvoice = signal(false);
        this.whatsappInvoiceSuccessful = signal(null);
        this.whatsappInvoiceNotice = signal("");
        this.whatsappReceiptSuccessful = signal(null);
        this.whatsappReceiptNotice = signal("");
    },
    isSendingReceipt: signal(false),
    isSendingInvoice: signal(false),
    whatsappInvoiceSuccessful: signal(null),
    whatsappInvoiceNotice: signal(""),
    whatsappReceiptSuccessful: signal(null),
    whatsappReceiptNotice: signal(""),

    async sendReceiptOnWhatsapp() {
        this.stopAutomaticSkip();
        if (this.loading() || this.isSendingReceipt() || this.isSendingInvoice()) {
            return;
        }
        this.whatsappReceiptSuccessful.set(null);
        this.whatsappReceiptNotice.set("");

        const partner = this.currentOrder ? this.currentOrder.getPartner() : null;
        const whatsappNumber = partner ? partner.whatsapp_number : null;
        if (!whatsappNumber) {
            this.whatsappReceiptSuccessful.set(false);
            this.whatsappReceiptNotice.set(_t("Wrong inputs detected. This may be due to whatsapp number is not given."));
            return;
        }

        if (!this.currentOrder.isSynced) {
            this.whatsappReceiptSuccessful.set(false);
            this.whatsappReceiptNotice.set(_t("This order is not yet synced to server. Make sure it is synced then try again."));
            return;
        }

        this.isSendingReceipt.set(true);
        try {
            await this.pos.data.call("pos.order", "action_send_receipt_whatsapp", [
                [this.currentOrder.id],
                whatsappNumber,
            ]);
            this.whatsappReceiptSuccessful.set(true);
            this.whatsappReceiptNotice.set(_t("Receipt sent to Whatsapp."));
        } catch (error) {
            this.whatsappReceiptSuccessful.set(false);
            const errorMsg = (error && error.data && error.data.message) || (error && error.message);
            this.whatsappReceiptNotice.set(errorMsg || _t("Sending message failed. Please try again."));
        } finally {
            this.isSendingReceipt.set(false);
        }
    },

    async sendInvoiceOnWhatsapp() {
        this.stopAutomaticSkip();
        if (this.loading() || this.isSendingInvoice() || this.isSendingReceipt()) {
            return;
        }
        this.whatsappInvoiceSuccessful.set(null);
        this.whatsappInvoiceNotice.set("");

        const partner = this.currentOrder ? this.currentOrder.getPartner() : null;
        const whatsappNumber = partner ? partner.whatsapp_number : null;
        if (!whatsappNumber) {
            this.whatsappInvoiceSuccessful.set(false);
            this.whatsappInvoiceNotice.set(_t("Wrong inputs detected. This may be due to whatsapp number is not given."));
            return;
        }

        if (!this.currentOrder.isSynced) {
            this.whatsappInvoiceSuccessful.set(false);
            this.whatsappInvoiceNotice.set(_t("This order is not yet synced to server. Make sure it is synced then try again."));
            return;
        }

        this.isSendingInvoice.set(true);
        try {
            await this.pos.data.call("pos.order", "action_send_invoice_whatsapp", [
                [this.currentOrder.id],
                whatsappNumber,
            ]);
            this.whatsappInvoiceSuccessful.set(true);
            this.whatsappInvoiceNotice.set(_t("Invoice sent to Whatsapp."));
        } catch (error) {
            this.whatsappInvoiceSuccessful.set(false);
            const errorMsg = (error && error.data && error.data.message) || (error && error.message);
            this.whatsappInvoiceNotice.set(errorMsg || _t("Wrong inputs detected. This may be due to incorrect API data entry or selecting the wrong session or whatsapp number is not given."));
        } finally {
            this.isSendingInvoice.set(false);
        }
    },
});
