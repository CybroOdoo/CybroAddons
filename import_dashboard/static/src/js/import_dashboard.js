/** @odoo-module **/
import { registry } from "@web/core/registry";
import { Component, useState , onMounted } from "@odoo/owl";
const actionRegistry = registry.category("actions");
import { useService } from "@web/core/utils/hooks";
/**
 * ImportDashBoard Component for displaying import options based on user permissions.
 */
export class ImportDashBoard extends Component {
    setup() {
        this.orm = useService("orm");
        super.setup(...arguments);
        this.state = useState({
            check_bill_of_material: false,
            check_pos: false,
            check_attendance: false,
            check_payment: false,
            check_task: false,
            check_sale: false,
            check_purchase: false,
            check_product: false,
            check_partner: false,
            check_entry: false,
            check_pricelist: false,
            check_vendor_pricelist: false,
        });
        this.action = useService("action");
        onMounted(async () => {
            await this.check_data();
        });
    }
    check_data() {
        /**
         * Show or hide tiles in the dashboard based on the state values.
         */
        const dashboardElement = this.__owl__.parent.children.ImportDashBoard__1.bdom.el;
        const cardBOMDiv = dashboardElement.querySelector('#card_bill_of_material');
        var result = this.orm.call('ir.config_parameter', 'check_user_group', []);
        result.then(res => {
            let showStartMsg = true; // Flag to track if start_msg should be shown
            const mapping = {
                bill_of_material: cardBOMDiv, // already defined element
                pos: '#card_pos',
                import_attendance: '#card_attendance',
                import_payment: '#card_payment',
                import_task: '#card_task',
                import_sale: '#card_sale',
                import_purchase: '#card_purchase',
                import_product_template: '#card_product',
                import_partner: '#card_partner',
                import_entry: '#card_entry',
                import_pricelist: '#card_pricelist',
                import_vendor_pricelist: '#card_vendor_pricelist',
            };
            Object.entries(mapping).forEach(([key, target]) => {
                const el = typeof target === 'string'
                    ? dashboardElement.querySelector(target)
                    : target;
                if (!el) return; // safety check
                const isVisible = !!res[key];
                el.style.display = isVisible ? 'block' : 'none';
                if (isVisible) {
                    showStartMsg = false;
                }
            });
            // Hide or show the start_msg element based on the flag
            const startMsgElement = dashboardElement.querySelector('.start_msg');
            if (showStartMsg) {
                startMsgElement.style.display = 'block';
            } else {
                startMsgElement.style.display = 'none';
            }
        });
    }
    // Define action methods for imports
    import_sale(ev) {
        /**
         * Opens the Import Sale Order form view.
         */
        this.action.doAction({
            name: "Import Sale Order",
            type: 'ir.actions.act_window',
            res_model: 'import.sale.order',
            view_mode: 'form',
            views: [[false, 'form']],
            target: 'new',
        });
    }
    import_purchase() {
        /**
         * Opens the Import Purchase Order form view.
         */
        this.action.doAction({
            name: "Import Purchase Order",
            type: 'ir.actions.act_window',
            res_model: 'import.purchase.order',
            view_mode: 'form',
            views: [[false, 'form']],
            target: 'new',
        });
    }
    import_entry() {
        /**
         * Opens the Import Journal Entry form view.
         */
        this.action.doAction({
            name: "Import Journal Entry",
            type: 'ir.actions.act_window',
            res_model: 'import.journal.entry',
            view_mode: 'form',
            views: [[false, 'form']],
            target: 'new',
        });
    }
    import_partner() {
        /**
         * Opens the Import Partner form view.
         */
        this.action.doAction({
            name: "Import Partner",
            type: 'ir.actions.act_window',
            res_model: 'import.partner',
            view_mode: 'form',
            views: [[false, 'form']],
            target: 'new',
        });
    }
    import_product_pricelist() {
        /**
         * Opens the Import Product Pricelist form view.
         */
        this.action.doAction({
            name: "Import Product Pricelist",
            type: 'ir.actions.act_window',
            res_model: 'import.product.pricelist',
            view_mode: 'form',
            views: [[false, 'form']],
            target: 'new',
        });
    }
    import_bill_of_material() {
        /**
         * Opens the Import Bill of Material form view.
         */
        this.action.doAction({
            name: "Import Bill of Material",
            type: 'ir.actions.act_window',
            res_model: 'import.bill.of.material',
            view_mode: 'form',
            views: [[false, 'form']],
            target: 'new',
        });
    }
    import_product_template() {
        /**
         * Opens the Import Product form view.
         */
        this.action.doAction({
            name: "Import Product",
            type: 'ir.actions.act_window',
            res_model: 'import.product.template',
            view_mode: 'form',
            views: [[false, 'form']],
            target: 'new',
        });
    }
    import_vendor_pricelist() {
        /**
         * Opens the Import Vendor Pricelist form view.
         */
        this.action.doAction({
            name: "Import Vendor Pricelist",
            type: 'ir.actions.act_window',
            res_model: 'import.vendor.pricelist',
            view_mode: 'form',
            views: [[false, 'form']],
            target: 'new',
        });
    }
    import_pos() {
        /**
         * Opens the Import POS form view.
         */
        this.action.doAction({
            name: "Import POS",
            type: 'ir.actions.act_window',
            res_model: 'import.pos.order',
            view_mode: 'form',
            views: [[false, 'form']],
            target: 'new',
        });
    }
    import_attendance() {
        /**
         * Opens the Import Attendance form view.
         */
        this.action.doAction({
            name: "Import Attendance",
            type: 'ir.actions.act_window',
            res_model: 'import.attendance',
            view_mode: 'form',
            views: [[false, 'form']],
            target: 'new',
        });
    }
    import_payment() {
        /**
         * Opens the Import Payment form view.
         */
        this.action.doAction({
            name: "Import Payment",
            type: 'ir.actions.act_window',
            res_model: 'import.payment',
            view_mode: 'form',
            views: [[false, 'form']],
            target: 'new',
        });
    }

    import_task() {
        /**
         * Opens the Import Task form view.
         */
        this.action.doAction({
            name: "Import Task",
            type: 'ir.actions.act_window',
            res_model: 'import.task',
            view_mode: 'form',
            views: [[false, 'form']],
            target: 'new',
        });
    }
    import_sales_pricelist() {
        /**
         * Opens the Import Sales Pricelist form view.
         */
        this.action.doAction({
            name: "Import Sales Pricelist",
            type: 'ir.actions.act_window',
            res_model: 'import.sales.pricelist',
            view_mode: 'form',
            views: [[false, 'form']],
            target: 'new',
        });
    }
    import_inventory() {
        /**
         * Opens the Import Inventory without Lot and Serial Number form view.
         */
        this.action.doAction({
            name: "Import Inventory without Lot and Serial Number",
            type: 'ir.actions.act_window',
            res_model: 'import.inventory',
            view_mode: 'form',
            views: [[false, 'form']],
            target: 'new',
        });
    }
    import_inventory_with_lot() {
        /**
         * Opens the Import Inventory with Lot and Serial Number form view.
         */
        this.action.doAction({
            name: "Import Inventory with Lot and Serial Number",
            type: 'ir.actions.act_window',
            res_model: 'import.inventory.with.lot',
            view_mode: 'form',
            views: [[false, 'form']],
            target: 'new',
        });
    }
}
// Register the ImportDashBoard component template
ImportDashBoard.template = "import_dashboard.ImportDashBoard";
// Add the ImportDashBoard component to the action registry
actionRegistry.add("import_dashboard_tag", ImportDashBoard);