/** @odoo-module */
import { patch } from "@web/core/utils/patch";
import { SendReceiptPopup } from "@point_of_sale/app/components/popups/send_receipt_popup/send_receipt_popup";
import { _t } from "@web/core/l10n/translation";

/**
 * Patch SendReceiptPopup to add WhatsApp sending options for receipts and invoices.
 */
patch(SendReceiptPopup.prototype, {
    setup() {
        super.setup();
        const partner = this.order.getPartner();
        this.state.phone = (partner && partner.whatsapp_number) || "";
    },

    showPhoneInput() {
        return super.showPhoneInput() || Boolean(this.pos.config.pos_whatsapp_enabled);
    },

    actionSendReceiptOnWhatsApp() {
        this.sendReceipt.call({
            action: "action_send_receipt_whatsapp",
            destination: this.state.phone,
            name: "WhatsApp Receipt",
        });
    },

    actionSendInvoiceOnWhatsApp() {
        this.sendReceipt.call({
            action: "action_send_invoice_whatsapp",
            destination: this.state.phone,
            name: "WhatsApp Invoice",
        });
    },

    get sendList() {
        const list = super.sendList;
        if (this.pos.config.pos_whatsapp_enabled) {
            const phoneItem = list.find((item) => item.model === "phone");
            if (phoneItem) {
                const applyMode = this.pos.config.apply_send_receipt_or_invoice;
                if (!applyMode || applyMode === "send_receipt" || applyMode === "both") {
                    phoneItem.buttons.push({
                        click: () => this.actionSendReceiptOnWhatsApp(),
                        status:
                            this.sendReceipt.lastArgs &&
                            this.sendReceipt.lastArgs[0] &&
                            this.sendReceipt.lastArgs[0].name === "WhatsApp Receipt" &&
                            this.sendReceipt.status,
                        icon: "oi_whatsapp",
                        iconClass: "text-success",
                        title: _t("Send Receipt via WhatsApp"),
                        disabled: () => !this.isValidPhone,
                    });
                }
                if (!applyMode || applyMode === "send_invoice" || applyMode === "both") {
                    phoneItem.buttons.push({
                        click: () => this.actionSendInvoiceOnWhatsApp(),
                        status:
                            this.sendReceipt.lastArgs &&
                            this.sendReceipt.lastArgs[0] &&
                            this.sendReceipt.lastArgs[0].name === "WhatsApp Invoice" &&
                            this.sendReceipt.status,
                        icon: "oi_whatsapp",
                        iconClass: "text-success",
                        title: _t("Send Invoice via WhatsApp"),
                        disabled: () => !this.isValidPhone,
                    });
                }
            }
        }
        return list;
    },
});
