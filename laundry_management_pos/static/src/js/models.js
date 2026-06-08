/** @odoo-module */
import { PosOrder } from "@point_of_sale/app/models/pos_order";
import { patch } from "@web/core/utils/patch";
import { PosOrderline } from "@point_of_sale/app/models/pos_order_line";
import { PaymentScreen } from "@point_of_sale/app/screens/payment_screen/payment_screen";
import { AlertDialog } from "@web/core/confirmation_dialog/confirmation_dialog";
import { _t } from "@web/core/l10n/translation";



patch(PosOrder.prototype, {
    /**
     * Override setPartner to prevent pricelist update when a washing type
     * has already been assigned to any orderline.
     */
    setPartner(partner) {
        this.assertEditable();
        this.update({ partner_id: partner });
        if (partner.company_type === "company") {
            this.set_to_invoice(true);
        }

        const lines = this.lines || [];
        const hasWashingType = lines.some(
            (line) => line.washing_type_id
        );

        if (!hasWashingType) {
            this.updatePricelistAndFiscalPosition(partner);
        }
    },
});

patch(PosOrderline.prototype, {
    /**
     * Function to set the service type of the Washing.
     */
    setWashingType(service) {
        this.washingType = service.name;
        this.washingType_id = service.id;
        this.washingType_price = service.amount;
        this.price_unit = service.amount;
        this.washing_type_id = service.id;
    },

    getDisplayClasses() {
        return {
            ...super.getDisplayClasses(),
            washingType: this.washing_type_id?.name,
            product_id: this.getProduct().id,
        };
    },

    /**
     * Function to get the washing type of the orderline.
     */
    get_washingType() {
        return this.washing_type_id || null;
    },

    /**
     * Merge orderlines only when they share the same washing type.
     */
    can_be_merged_with(orderline) {
        const thisType = this.get_washingType();
        const otherType = orderline.get_washingType();
        if ((thisType?.id || null) !== (otherType?.id || null)) {
            return false;
        }
        return super.can_be_merged_with(orderline);
    },

    /**
     * Clone the orderline including its washing type data.
     */
    clone() {
        const orderline = super.clone(...arguments);
        orderline.washingType = this.washingType;
        orderline.washingType_id = this.washingType_id;
        orderline.washingType_price = this.washingType_price;
        if (this.washingType_price) {
            orderline.price_unit = this.washingType_price;
        }
        return orderline;
    },

    get washingTypeName() {
        return this.washing_type_id?.name || null;
    },
});

patch(PaymentScreen.prototype, {
    async validateOrder(isForceValidate = false) {
        if (!this.currentOrder.getPartner()) {
            this.dialog.add(AlertDialog, {
                title: _t("Customer Required"),
                body: _t("Please select a customer before validating the order."),
            });
            return;
        }
        return super.validateOrder(...arguments);
    }
});

