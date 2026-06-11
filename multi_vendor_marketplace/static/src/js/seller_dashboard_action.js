/** @odoo-module **/

import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { Component, onWillStart } from "@odoo/owl";

export class SellerDashboard extends Component {
    setup() {
        this.action = useService("action");
        this.rpc = useService("rpc");
        this.dashboardData = {};

        onWillStart(async () => {
            this.dashboardData = await this.rpc("/seller_dashboard");
        });
    }

    async onProductPendingClick() {
        await this.action.doAction({
            name: 'Product Pending',
            type: 'ir.actions.act_window',
            res_model: 'product.template',
            view_mode: 'kanban',
            views: [[this.dashboardData.product_kanban_id, 'kanban']],
            domain: [['state', '=', 'pending']],
        });
    }

    async onProductApprovedClick() {
        await this.action.doAction({
            name: 'Product Approved',
            type: 'ir.actions.act_window',
            res_model: 'product.template',
            view_mode: 'kanban',
            views: [[this.dashboardData.product_kanban_id, 'kanban']],
            domain: [['state', '=', 'approved']],
        });
    }

    async onProductRejectedClick() {
        await this.action.doAction({
            name: 'Product Rejected',
            type: 'ir.actions.act_window',
            res_model: 'product.template',
            view_mode: 'kanban',
            views: [[this.dashboardData.product_kanban_id, 'kanban']],
            domain: [['state', '=', 'rejected']],
        });
    }

    async onSellerRejectedClick() {
        await this.action.doAction({
            name: 'Seller Rejected',
            type: 'ir.actions.act_window',
            res_model: 'res.partner',
            view_mode: 'kanban,form',
            views: [[false, 'kanban'], [false, 'form']],
            domain: [['state', '=', 'Denied']],
        });
    }

    async onSellerApprovedClick() {
        await this.action.doAction({
            name: 'Seller Approved',
            type: 'ir.actions.act_window',
            res_model: 'res.partner',
            view_mode: 'kanban,form',
            views: [[false, 'kanban'], [false, 'form']],
            domain: [['state', '=', 'Approved']],
        });
    }

    async onSellerPendingClick() {
        await this.action.doAction({
            name: 'Seller Pending',
            type: 'ir.actions.act_window',
            res_model: 'res.partner',
            view_mode: 'kanban,form',
            views: [[false, 'kanban'], [false, 'form']],
            domain: [['state', '=', 'Pending for Approval']],
        });
    }

    async onInvReqPendingClick() {
        await this.action.doAction({
            name: 'Inventory Request Pending',
            type: 'ir.actions.act_window',
            res_model: 'inventory.request',
            view_mode: 'kanban,form',
            views: [[false, 'kanban'], [false, 'form']],
            domain: [['state', '=', 'Requested']],
        });
    }

    async onInvReqApprovedClick() {
        await this.action.doAction({
            name: 'Inventory Request Approved',
            type: 'ir.actions.act_window',
            res_model: 'inventory.request',
            view_mode: 'kanban,form',
            views: [[false, 'kanban'], [false, 'form']],
            domain: [['state', '=', 'Approved']],
        });
    }

    async onInvReqRejectedClick() {
        await this.action.doAction({
            name: 'Inventory Request Rejected',
            type: 'ir.actions.act_window',
            res_model: 'inventory.request',
            view_mode: 'kanban,form',
            views: [[false, 'kanban'], [false, 'form']],
            domain: [['state', '=', 'Rejected']],
        });
    }

    async onPaymentPendingClick() {
        await this.action.doAction({
            name: 'Payment Request Pending',
            type: 'ir.actions.act_window',
            res_model: 'seller.payment',
            view_mode: 'kanban,form',
            views: [[false, 'kanban'], [false, 'form']],
            domain: [['state', '=', 'Requested']],
        });
    }

    async onPaymentApprovedClick() {
        await this.action.doAction({
            name: 'Payment Request Approved',
            type: 'ir.actions.act_window',
            res_model: 'seller.payment',
            view_mode: 'kanban,form',
            views: [[false, 'kanban'], [false, 'form']],
            domain: [['state', '=', 'Validated']],
        });
    }

    async onPaymentRejectedClick() {
        await this.action.doAction({
            name: 'Payment Request Rejected',
            type: 'ir.actions.act_window',
            res_model: 'seller.payment',
            view_mode: 'kanban,form',
            views: [[false, 'kanban'], [false, 'form']],
            domain: [['state', '=', 'Rejected']],
        });
    }

    async onOrderPendingClick() {
        await this.action.doAction({
            name: 'Sale Order Pending',
            type: 'ir.actions.act_window',
            res_model: 'sale.order.line',
            view_mode: 'kanban,form',
            views: [[this.dashboardData.sale_order_kanban_id, 'kanban'], [this.dashboardData.sale_order_form_id, 'form']],
            domain: [['state', '=', 'pending']],
        });
    }

    async onOrderApprovedClick() {
        await this.action.doAction({
            name: 'Sale Order Approved',
            type: 'ir.actions.act_window',
            res_model: 'sale.order.line',
            view_mode: 'kanban,form',
            views: [[this.dashboardData.sale_order_kanban_id, 'kanban'], [this.dashboardData.sale_order_form_id, 'form']],
            domain: [['state', '=', 'approved']],
        });
    }

    async onOrderShippedClick() {
        await this.action.doAction({
            name: 'Sale Order Shipped',
            type: 'ir.actions.act_window',
            res_model: 'sale.order.line',
            view_mode: 'kanban,form',
            views: [[this.dashboardData.sale_order_kanban_id, 'kanban'], [this.dashboardData.sale_order_form_id, 'form']],
            domain: [['state', '=', 'shipped']],
        });
    }

    async onOrderCancelClick() {
        await this.action.doAction({
            name: 'Sale Order cancelled',
            type: 'ir.actions.act_window',
            res_model: 'sale.order.line',
            view_mode: 'kanban,form',
            views: [[this.dashboardData.sale_order_kanban_id, 'kanban'], [this.dashboardData.sale_order_form_id, 'form']],
            domain: [['state', '=', 'cancel']],
        });
    }
}

SellerDashboard.template = "multi_vendor_marketplace.SellerDashBoard";

registry.category("actions").add("seller_dashboard_tag", SellerDashboard);
