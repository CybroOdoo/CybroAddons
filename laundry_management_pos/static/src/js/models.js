/** @odoo-module */
import { PosOrder } from "@point_of_sale/app/models/pos_order";
import { patch } from "@web/core/utils/patch";
import { Orderline } from "@point_of_sale/app/generic_components/orderline/orderline";
import { PosOrderline } from "@point_of_sale/app/models/pos_order_line";
import { _t } from "@web/core/l10n/translation";
import { LaundryServiceTypePopup } from "@laundry_management_pos/js/popup/washing_type_popup";

/**
 * Patch PosOrder to handle partner updates and pricelist changes
 * based on whether laundry services are present.
 */
patch(PosOrder.prototype, {
    /**
     * Set the partner for the order and update price lists if no washing type is selected.
     * @param {Object} partner - The partner to set.
     */
    set_partner(partner) {
        // Keep original Odoo behavior
        this.assert_editable();
        this.update({ partner_id: partner });
        if (partner.company_type == "company") {
            this.set_to_invoice(true);
        }
        let washing = 0;
        const lines = this.orderlines?.models || [];
        const order = this.lines[0].washing_type_id.id;

        for (const line of lines) {
            if (order) {
                washing = 1;
                break;
            }
            if (washing == 0) {
                this.updatePricelistAndFiscalPosition(partner);
            }
        }
    },
});


/**
 * Patch PosOrderline to include laundry-specific properties and logic.
 */
patch(PosOrderline.prototype, {
    /**
     * Setup the orderline with mandatory laundry fields.
     */
    setup() {
        super.setup(...arguments);
        const data = arguments[1] || {};
        this.washing_type = data.washing_type || null;
        this.washing_type_id_custom = data.washing_type_id_custom || null;
        this.washing_type_price = data.washing_type_price || 0.0;
    },

    /**
     * Function to set the service type of the Washing.
     * @param {Object} service - The washing service details.
     */
    setWashingType(service) {
        this.washing_type = service.name;
        this.washing_type_id_custom = service.id;
        this.washing_type_price = service.amount;
        this.price_unit = service.amount;
        this.washing_type_id = service.id;
    },
    /**
     * Get data for display in the UI.
     * @returns {Object} - The display data.
     */
    getDisplayData() {
        return {
            ...super.getDisplayData(),
            washing_type: this.washing_type_id?.name,
            product_id: this.get_product().id,
        };
    },
    /**
     * Function to get the service type of the Washing.
     * @returns {Object} - The washing type ID.
     */
    get_washing_type(e) {
        return this.washing_type_id;
    },
    /**
     * Determine if this orderline can be merged with another.
     * @param {Object} orderline - The other orderline.
     * @returns {boolean} - True if mergable.
     */
    can_be_merged_with(orderline) {
        if (orderline.get_washing_type() !== this.get_washing_type()) {
            return false;
        } else {
            return super.can_be_merged_with(orderline);
        }
    },

    /**
     * Clone the service with order-lines.
     * @returns {Object} - Cloned orderline.
     */
    clone() {
        const orderline = super.clone(...arguments);
        orderline.washing_type = this.washing_type;
        orderline.washing_type_id_custom = this.washing_type_id_custom;
        orderline.washing_type_price = this.washing_type_price;
        if (this.washing_type_price) {
            orderline.price = this.washing_type_price;
        }
        return orderline;
    },

    /**
     * Export as JSON for backend.
     * @returns {Object} - JSON representation.
     */
    export_as_JSON() {
        var json = super.export_as_JSON();
        json.washing_type = this.washing_type;
        json.washing_type_id_custom = this.washing_type_id_custom;
        json.washing_type_price = this.washing_type_price;
        if (this.washing_type_price) {
            json.price = this.washing_type_price;
        }
        return json;
    },
    /**
     * Method for adding the washing type details.
     * @param {Object} json - JSON data.
     */
    init_from_JSON(json) {
        super.init_from_JSON(...arguments);
        this.washing_type = json.washing_type;
        this.washing_type_id_custom = json.washing_type_id_custom;
        this.washing_type_price = json.washing_type_price;
    },
    /**
     * Click function of Laundry Service button.
     * @param {Event} e - Click event.
     */
     click(e) {
        this.popup.add(LaundryServiceTypePopup, {
            title: _t('Laundry Service'),
            body: _t('Choose the Washing type'),
            service: this.pos.washing_type,
            pos: this.pos,
            orderline: this.props.line,
        })
    },
    /**
     * Override set_partner method to prevent updating price.
     * @param {Object} partner - The partner.
     */
    set_partner(partner) {
        this.assert_editable();
        this.partner = partner;
        var washing=0
        for (let line of this.currentOrder.orderlines) {
           if (line.get_washing_type())
           {
                washing=1
           }
        }
        if (washing==0)
        {
            this.updatePricelistAndFiscalPosition(partner);
        }
    }
});

patch(Orderline, {
    props: {
        ...Orderline.props,
        line: {
            ...Orderline.props.line,
            shape: {
                ...Orderline.props.line.shape,
                washing_type: { type: String, optional: true },
                product_id: { type: Number, optional: true },
            },
        },
    },
});

