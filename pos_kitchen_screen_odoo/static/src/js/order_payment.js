/** @odoo-module **/

import { Order } from "@point_of_sale/app/store/models";
import { patch } from "@web/core/utils/patch";
import { ErrorPopup } from "@point_of_sale/app/errors/popups/error_popup";
import { _t } from "@web/core/l10n/translation";
const { Component, useState } = owl;
import { useService } from "@web/core/utils/hooks";
import { jsonrpc } from "@web/core/network/rpc_service";

/**
 * Patching the Order class to add custom functionality.
 */
patch(Order.prototype, {
    setup(_defaultObj, options) {
        super.setup(...arguments);
        this.orm = options.pos.orm;
        this.popup = options.pos.popup;
        this.kitchen = true;
    },
    /**
     * Override of the pay method to handle payment logic.
     */
    async pay() {
        var order_name = this.pos.selectedOrder.name;
        var self = this;
        await this.orm.call("pos.order", "check_order", ["", order_name]).then(function (result) {
            if (result.category) {
                var title = "No category found for your current order in the kitchen.(" + result.category + ')';
                self.kitchen = false;
                self.popup.add(ErrorPopup, {
                    title: _t(title),
                    body: _t("No food items found for the specified category for this kitchen. Kindly remove the selected food and update the order by clicking the 'Order' button. Following that, proceed with the payment."),
                });
            } else if (result == true) {
                self.kitchen = false;
                self.popup.add(ErrorPopup, {
                    title: _t("Food is not ready"),
                    body: _t("Please Complete all the food first."),
                });
            } else {
                self.kitchen = true;
            }
        });

        if (!this.orderlines.length) {
            return;
        }

        if (
            this.orderlines.some(
                (line) => line.get_product().tracking !== "none" && !line.has_valid_product_lot()
            ) &&
            (this.pos.picking_type.use_create_lots || this.pos.picking_type.use_existing_lots)
        ) {
            const { confirmed } = await this.env.services.popup.add(ConfirmPopup, {
                title: _t("Some Serial/Lot Numbers are missing"),
                body: _t(
                    "You are trying to sell products with serial/lot numbers, but some of them are not set.\nWould you like to proceed anyway?"
                ),
                confirmText: _t("Yes"),
                cancelText: _t("No"),
            });

            if (confirmed) {
                if (this.kitchen) {
                    this.pos.mobile_pane = "right";
                    this.env.services.pos.showScreen("PaymentScreen");
                }
            }
        } else {
            if (this.kitchen) {
                this.pos.mobile_pane = "right";
                this.env.services.pos.showScreen("PaymentScreen");
            }
        }
    }
});
