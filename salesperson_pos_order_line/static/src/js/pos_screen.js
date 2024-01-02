/** @odoo-module **/
import { ProductScreen } from "@point_of_sale/app/screens/product_screen/product_screen";
import { Component } from "@odoo/owl";
import { usePos } from "@point_of_sale/app/store/pos_hook";
import { _t } from "@web/core/l10n/translation";
import { SelectionPopup } from "@point_of_sale/app/utils/input_popups/selection_popup";

export class SetProductListButton extends Component {
    setup() {
    super.setup();
this.pos = usePos();
 const { popup } = this.env.services;
        this.popup = popup;
    }
    get productsList() {
        let list = [];
        list = this.pos.db.get_product_by_category(
            this.pos.selectedCategoryId
        );
        return list.sort(function(a, b) {
            return a.display_name.localeCompare(b.display_name);
        });
    }
   async onClick() {
            let list = this.productsList;
            const salespersonList = this.pos.res_users.map((salesperson) => {
                    return {
                        id: salesperson.id,
                        item: salesperson,
                        label: salesperson.name,
                        isSelected: false,
                    };
                });
              const { confirmed, payload: salesperson } = await this.popup.add(SelectionPopup, {
                title: _t("Select the Salesperson"),
                list: salespersonList,
            });
              if (confirmed) {
             this.pos.selectedOrder.selected_orderline.salesperson = salesperson.name;
             this.pos.selectedOrder.selected_orderline.user_id = salesperson.id;
        }
    }
}
SetProductListButton.template = "SalesPersonButton";
ProductScreen.addControlButton({
    component: SetProductListButton,
    condition: function() {
        return true;
    },
});
