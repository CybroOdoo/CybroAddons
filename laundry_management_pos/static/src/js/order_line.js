/** @odoo-module */
import { Orderline } from "@point_of_sale/app/generic_components/orderline/orderline";
import { patch } from "@web/core/utils/patch";
import { usePos } from "@point_of_sale/app/store/pos_hook";
import { useService } from "@web/core/utils/hooks";
import { _t } from "@web/core/l10n/translation";
import { LaundryServiceTypePopup } from "@laundry_management_pos/js/popup/washing_type_popup";

patch(Orderline.prototype, {
    setup() {
        super.setup(...arguments);
        this.pos = usePos();
        this.popup = useService("popup");
    },
    // Button click function to open the popup
     click(e) {
        this.popup.add(LaundryServiceTypePopup, {
            title: _t('Laundry Service'),
            body: _t('Choose the Washing type'),
            service: this.pos.washing_type,
            pos: this.pos,
            orderline: this.props.line,
        })
    },
     // Function to set the service type of the Washing
    set_washingType(service) {
        this.washingType = service.name;
        this.washingType_id = service.id;
        this.washingType_price = service.amount;
        this.price = service.amount;
    },
    //Method for removing laundry
    remove_laundry() {
        this.props.line.washingType = '';
        this.props.line.washingType_id = 0.0;
        this.props.line.washingType_price = 0.0;
        var order = this.pos.get_order();
        if (order)
        {
            order.selected_orderline.washingType='';
            order.selected_orderline.washingType_id=0.0;
            order.selected_orderline.washingType_price=0.0;
            order.updatePricelistAndFiscalPosition(order.partner);
            for (const line of order.orderlines) {
                if (line.washingType!="")
                {
                    line.price=line.washingType_price
                }
            }
        }
    },
    //Override init to add washing type details
    init_from_JSON(json) {
        super.init_from_JSON(...arguments);
        this.washingType = json.washingType;
        this.washingType_id = json.washingType_id;
        this.washingType_price = json.washingType_price;
    },
});
