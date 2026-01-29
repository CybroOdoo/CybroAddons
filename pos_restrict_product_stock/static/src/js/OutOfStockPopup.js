/** @odoo-module **/
/*
 * This file is used to store a popup for stocks out of stock for forced orders.
 */
import AbstractAwaitablePopup from 'point_of_sale.AbstractAwaitablePopup';
import Registries from 'point_of_sale.Registries';

class OutOfStockPopup extends AbstractAwaitablePopup {
}
OutOfStockPopup.template = 'OutOfStockPopup';
Registries.Component.add(OutOfStockPopup);