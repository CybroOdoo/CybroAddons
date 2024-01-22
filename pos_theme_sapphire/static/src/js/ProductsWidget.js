/** @odoo-module **/

import { ProductsWidget } from "@point_of_sale/app/screens/product_screen/product_list/product_list";
import { CashierName } from "@point_of_sale/app/navbar/cashier_name/cashier_name";

ProductsWidget.components = {
    ...ProductsWidget.components,
    CashierName,
}
