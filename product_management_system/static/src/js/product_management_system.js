/** @odoo-module **/
import { useService } from "@web/core/utils/hooks";
import { KanbanController } from "@web/views/kanban/kanban_controller";
import { kanbanView } from "@web/views/kanban/kanban_view";
import { registry } from "@web/core/registry";
import { useState, useEffect } from "@odoo/owl";

export class KanbanButton extends KanbanController {
    static template = 'button_in_kanban.button';
    setup() {
        super.setup();
        this.actionService = useService("action");
        this.state = useState({
            products_selected: [],
        });
        useEffect(() => {
            this.check_selected();
            const handleClick = (ev) => {
                if (ev.target.classList.contains('product_check_box')) {
                    this._onSelectDocs(ev);
                }
            };
            if (this.rootRef.el) {
                this.rootRef.el.addEventListener('click', handleClick);
                return () => this.rootRef.el.removeEventListener('click', handleClick);
            }
        });
    }

    check_selected() {
        if (this.rootRef.el) {
            const productDivs = this.rootRef.el.querySelectorAll('.oe_kanban_details');
            productDivs.forEach(div => {
                const productId = parseInt(div.id);
                const checkbox = div.querySelector('.product_check_box');
                if (checkbox) {
                    checkbox.checked = this.state.products_selected.includes(productId);
                }
            });
        }
    }

    _onSelectDocs(ev) {
        const checked = ev.target.checked;
        const recordId = parseInt(ev.target.dataset.id);
        this.state.products_selected = checked
            ? [...this.state.products_selected, recordId]
            : this.state.products_selected.filter(id => id !== recordId);
        const toast = document.querySelector('.toast');
        if (this.state.products_selected.length > 0) {
            toast.classList.add('show');
            toast.style.display = 'inline';
        } else {
            toast.style.display = '';
            toast.classList.remove('show');
        }
    }

    _onChangeCategory(){
    //    Function for changing category of selected products
        this.actionService.doAction({
            type: 'ir.actions.act_window',
            name: 'Change Category',
            res_model: 'product.category.change',
            view_mode: 'form',
            views: [[false, 'form']],
            target: 'new',
            context: {
                'default_product_ids': this.state.products_selected,
            },
        });
    }

    _onCustLeadTimeProducts (){
    //    Function for changing Customer Lead Time of selected products
        this.actionService.doAction({
            type: 'ir.actions.act_window',
            name: 'Change Customer Lead Time',
            res_model: 'product.customer.lead.time',
            view_mode: 'form',
            views: [[false, 'form']],
            target: 'new',
            context: {
                'default_product_ids': this.state.products_selected,
            },
        });
    }

    _onArchiveProducts (ev){
    //    Function for changing Archive Product of selected products
        this.actionService.doAction({
            type: 'ir.actions.act_window',
            name: 'Archive Product',
            res_model: 'product.archive',
            view_mode: 'form',
            views: [[false, 'form']],
            target: 'new',
            context: {
                'default_product_ids': this.state.products_selected,
            },
        });
    }

    _onUpdatePrice (){
    //    Function for changing Update Price of selected products
        this.actionService.doAction({
            type: 'ir.actions.act_window',
            name: 'Update Price',
            res_model: 'product.update.price',
            view_mode: 'form',
            views: [[false, 'form']],
            target: 'new',
            context: {
                'default_product_ids': this.state.products_selected,
            },
        });
    }

    _onAddVendor (){
    //    Function for changing Add Vendor of selected products
        this.actionService.doAction({
            type: 'ir.actions.act_window',
            name: 'Add Vendor',
            res_model: 'product.add.vendor',
            view_mode: 'form',
            views: [[false, 'form']],
            target: 'new',
            context: {
                'default_product_ids': this.state.products_selected,
            },
        });
    }

    _onMakeSalable (){
        //    Function for Make Salable of selected products
        this.actionService.doAction({
            type: 'ir.actions.act_window',
            name: 'Make Products Salable',
            res_model: 'product.make.salable',
            view_mode: 'form',
            views: [[false, 'form']],
            target: 'new',
            context: {
                'default_product_ids': this.state.products_selected,
            },
        });
    }

    _onMakePurchasable (){
    //    Function for Make Purchasable of selected products
        this.actionService.doAction({
            type: 'ir.actions.act_window',
            name: 'Make Products Purchasable',
            res_model: 'product.make.purchasable',
            view_mode: 'form',
            views: [[false, 'form']],
            target: 'new',
            context: {
                'default_product_ids': this.state.products_selected,
            },
        });
    }

    _onDeleteProducts (){
    //    Function for Deleting the selected products
        this.actionService.doAction({
            type: 'ir.actions.act_window',
            name: 'Delete Product',
            res_model: 'product.delete',
            view_mode: 'form',
            views: [[false, 'form']],
            target: 'new',
            context: {
                'default_product_ids': this.state.products_selected,
            },
        });
    }

    _onPublishProducts (){
    //    Function for Publish On Website of selected products
        this.actionService.doAction({
            type: 'ir.actions.act_window',
            name: 'Publish On Website',
            res_model: 'product.publish',
            view_mode: 'form',
            views: [[false, 'form']],
            target: 'new',
            context: {
                'default_product_ids': this.state.products_selected,
            },
        });
    }

    _onAlternativeProducts (){
    //    Function for Adding Alternative Product of selected products
        this.actionService.doAction({
            type: 'ir.actions.act_window',
            name: 'Add Alternative Product',
            res_model: 'product.alternative',
            view_mode: 'form',
            views: [[false, 'form']],
            target: 'new',
            context: {
                'default_product_ids': this.state.products_selected,
            },
        });
    }

    _onAccessoryProducts (){
    //    Function for Adding Accessory Product of selected products
        this.actionService.doAction({
            type: 'ir.actions.act_window',
            name: 'Add Accessory Product',
            res_model: 'product.accessory',
            view_mode: 'form',
            views: [[false, 'form']],
            target: 'new',
            context: {
                'default_product_ids': this.state.products_selected,
            },
        });
    }

    _onOptionalProducts (){
    //    Function for Adding Optional Product of selected products
        this.actionService.doAction({
            type: 'ir.actions.act_window',
            name: 'Add Optional Product',
            res_model: 'product.optional',
            view_mode: 'form',
            views: [[false, 'form']],
            target: 'new',
            context: {
                'default_product_ids': this.state.products_selected,
            },
        });
    }

    _onEditInvoicePolicyProducts (){
    //    Function for Editing Invoice Policy of selected products
        this.actionService.doAction({
            type: 'ir.actions.act_window',
            name: 'Edit Invoice Policy',
            res_model: 'product.invoice',
            view_mode: 'form',
            views: [[false, 'form']],
            target: 'new',
            context: {
                'default_product_ids': this.state.products_selected,
            },
        });
    }

    _onAddCustomerTaxProducts (){
    //    Function for Changing Customer Tax of selected products
        this.actionService.doAction({
            type: 'ir.actions.act_window',
            name: 'Change Customer Tax',
            res_model: 'product.customer.tax',
            view_mode: 'form',
            views: [[false, 'form']],
            target: 'new',
            context: {
                'default_product_ids': this.state.products_selected,
            },
        });
    }

    _onAddVendorTaxProducts (){
    //    Function for Changing Vendor Tax of selected products
        this.actionService.doAction({
            type: 'ir.actions.act_window',
            name: 'Change Vendor Tax',
            res_model: 'product.vendor.tax',
            view_mode: 'form',
            views: [[false, 'form']],
            target: 'new',
            context: {
                'default_product_ids': this.state.products_selected,
            },
        });
    }

    _onWebCategChangeProducts (){
    //    Function for Changing Category On Website of selected products
        this.actionService.doAction({
            type: 'ir.actions.act_window',
            name: 'Change Category On Website',
            res_model: 'product.category.website',
            view_mode: 'form',
            views: [[false, 'form']],
            target: 'new',
            context: {
                'default_product_ids': this.state.products_selected,
            },
        });
    }

    _onAddAttributeProducts (){
    //    Function for Adding Product Attributes of selected products
        this.actionService.doAction({
            type: 'ir.actions.act_window',
            name: 'Add Product Attributes',
            res_model: 'product.add.attribute',
            view_mode: 'form',
            views: [[false, 'form']],
            target: 'new',
            context: {
                'default_product_ids': this.state.products_selected,
            },
        });
    }

    _onChangeTrackingProducts (){
    //    Function for Changing Product Tracking of selected products
        this.actionService.doAction({
            type: 'ir.actions.act_window',
            name: 'Change Product Tracking',
            res_model: 'product.change.tracking',
            view_mode: 'form',
            views: [[false, 'form']],
            target: 'new',
            context: {
                'default_product_ids': this.state.products_selected,
            },
        });
    }

    _onChangeProductionLocation (){
    //    Function for Changing Production Location of selected products
        this.actionService.doAction({
            type: 'ir.actions.act_window',
            name: 'Change Production Location',
            res_model: 'product.production.location',
            view_mode: 'form',
            views: [[false, 'form']],
            target: 'new',
            context: {
                'default_product_ids': this.state.products_selected,
            },
        });
    }

    _onChangeInventoryLocation (){
    //    Function for Changing Inventory Location of selected products
        this.actionService.doAction({
            type: 'ir.actions.act_window',
            name: 'Change Inventory Location',
            res_model: 'product.inventory.location',
            view_mode: 'form',
            views: [[false, 'form']],
            target: 'new',
            context: {
                'default_product_ids': this.state.products_selected,
            },
        });
    }
}

const ProductKanbanView = {
    ...kanbanView,
    Controller: KanbanButton,
};

registry.category("views").add("product_management_kanban_view", ProductKanbanView);
