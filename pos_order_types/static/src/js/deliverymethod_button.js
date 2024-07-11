/** @odoo-module */
    import { Component } from "@odoo/owl";
    import { _t } from "@web/core/l10n/translation";
    import { usePos } from "@point_of_sale/app/store/pos_hook";
    import { ProductScreen } from "@point_of_sale/app/screens/product_screen/product_screen";
    import { SelectionPopup } from "@point_of_sale/app/utils/input_popups/selection_popup";
    import { useService } from "@web/core/utils/hooks";

    const { useState, useRef } = owl;
    var delivery_type = {}
class SetDeliveryMethodButton extends Component {
   setup() {
           super.setup();
           this.pos = usePos();
           this.popup = useService("popup")

           this.state = useState({
                name: this.get_current_delivery_method_name()
                })
        }
        async button_click() {
                var orders = this.pos.orders;
                var no_delivery_method = [{
            }];
            const currentdelivery_method = this.pos.get_order().delivery_method
            const selection_list = [];
            for (let del_meth of this.pos.delivery_type) {
                selection_list.push({
                    id: del_meth.id,
                    label: del_meth.name,
                    isSelected: currentdelivery_method
                        ? del_meth.id === currentdelivery_method.id
                        : false,
                    item: del_meth,
                });
            }
            //            Selection Popup shows given delivery method
            if (selection_list.length>0){
                    const { confirmed, payload: selected_delivery_method } = await this.popup.add(SelectionPopup, {
                        title: _t("Please select a product for this reward"),
                        list: selection_list,
                    });
                    if (confirmed) {
                            var order = this.pos.get_order();
                            order.delivery_method = selected_delivery_method;
                            var store_type= JSON.parse(localStorage.getItem(this.pos.db.name + 'order_type_reload')) || {};
                            store_type[this.pos.get_order().uid] = {'type': selected_delivery_method}
                            localStorage.setItem('order_type_reload',JSON.stringify(store_type));
                            if (selected_delivery_method!= undefined)
                              {
                            this.state.name =order.delivery_method.name;
                            }
                    }
                               }
        }
        get_current_delivery_method_name(){
             var name = _t('Order Types');
            var item = localStorage.getItem(this.pos.db.name + 'order_type_reload')
            var obj=JSON.parse(item)
            var order_type = false
            if (obj){
                if (this.pos.get_order().uid in obj)
                order_type = obj[this.pos.get_order().uid]
                if (this.pos.get_order().orderlines.length ==0)
                {
                         name = _t('Order Types');
                }else if (order_type ){
                    if ('type' in order_type){
                        name = order_type.type.name;
                        this.pos.get_order().delivery_method= order_type.type;
                    }
                }
                return name;
            }
        }
}
//Added the button Order types
SetDeliveryMethodButton.template = 'SetDeliveryMethodButton';
ProductScreen.addControlButton({
        component: SetDeliveryMethodButton,
        condition: function () {
            return true;
        },
        position: ['before', 'SetPricelistButton'],
    });
