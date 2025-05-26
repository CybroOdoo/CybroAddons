/** @odoo-module */
import { Order, Orderline } from "@point_of_sale/app/store/models";
import { patch } from "@web/core/utils/patch";

patch(Order.prototype, {
    set_partner(partner) {
        this.assert_editable();
        this.partner = partner;
        var washing=0
        for (let line of this.orderlines) {
            if (line.get_washingType())
            {
                washing=1
            }
        }
        if (washing==0)
        {
            this.updatePricelistAndFiscalPosition(partner);
        }
    },
});

patch(Orderline.prototype, {
    setup() {
        super.setup(...arguments);
        this.washingType = this.washingType || arguments[1].washingType;
        this.washingType_id = this.washingType_id;
        this.washingType_price = this.washingType_id || 0.0;
    },
    // Function to set the service type of the Washing
    set_washingType(service) {
        this.washingType = service.name;
        this.washingType_id = service.id;
        this.washingType_price = service.amount;
        this.price = service.amount;
    },
    getDisplayData() {
    /**Add the washingType and image**/
        return {
        	...super.getDisplayData(),
        	washingType: this.get_washingType(),
        	product_id: this.get_product().id,
        };
    },
    // Function to get the service type of the Washing
    get_washingType(e) {
        return this.washingType;
    },
     // when we add an new orderline we want to merge it with the last line to see reduce the number of items based on the selected washing types
    // in the orderline. This returns true if it makes sense to merge the two
    can_be_merged_with(orderline) {
        if (orderline.get_washingType() !== this.get_washingType()) {
            return false;
        } else {
            return super.can_be_merged_with(orderline);
        }
    },
    // Clone the service with order-lines
    clone() {
        var orderline = super.clone();
        orderline.washingType = this.washingType;
        orderline.washingType_id = this.washingType_id;
        orderline.washingType_price = this.washingType_price;
        if (this.washingType_price) {
            orderline.price = this.washingType_price;
        }
        return orderline;
    },
    //Method for exports as JSON
    export_as_JSON() {
        var json = super.export_as_JSON();
        json.washingType = this.washingType;
        json.washingType_id = this.washingType_id;
        json.washingType_price = this.washingType_price;
        if (this.washingType_price) {
            json.price = this.washingType_price;
        }
        return json;
    },
    //Method for adding the washing type details
    init_from_JSON(json) {
        super.init_from_JSON(...arguments);
        this.washingType = json.washingType;
        this.washingType_id = json.washingType_id;
        this.washingType_price = json.washingType_price;
    },
    //Click function of Laundry Service button
     click(e) {
        this.popup.add(LaundryServiceTypePopup, {
            title: _t('Laundry Service'),
            body: _t('Choose the Washing type'),
            service: this.pos.washing_type,
            pos: this.pos,
            orderline: this.props.line,
        })
    },
    //Override set_partner method to prevent updating price
    set_partner(partner) {
        this.assert_editable();
        this.partner = partner;
        var washing=0
        for (let line of this.currentOrder.orderlines) {
           if (line.get_washingType())
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
