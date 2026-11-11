/** @odoo-module **/
import { useService } from "@web/core/utils/hooks";
import { KanbanController } from "@web/views/kanban/kanban_controller";
import { kanbanView } from "@web/views/kanban/kanban_view";
import { FormController } from "@web/views/form/form_controller";
import { registry } from "@web/core/registry";
import { patch } from "@web/core/utils/patch";
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
            const checkboxes = this.rootRef.el.querySelectorAll('.product_check_box');
            checkboxes.forEach(checkbox => {
                const productId = parseInt(checkbox.dataset.id);
                checkbox.checked = this.state.products_selected.includes(productId);
            });
        }
    }

    _onSelectDocs(ev) {
        const checked = ev.target.checked;
        const recordId = parseInt(ev.target.dataset.id);
        this.state.products_selected = checked
            ? [...this.state.products_selected, recordId]
            : this.state.products_selected.filter(id => id !== recordId);
        const toast = (this.rootRef.el && this.rootRef.el.querySelector('.toast')) || document.querySelector('.toast');
        if (toast) {
            if (this.state.products_selected.length > 0) {
                toast.classList.add('show');
                toast.style.display = 'inline';
            } else {
                toast.style.display = '';
                toast.classList.remove('show');
            }
        }
    }

    _resetSelection() {
        this.state.products_selected = [];
        const toast = (this.rootRef.el && this.rootRef.el.querySelector('.toast')) || document.querySelector('.toast');
        if (toast) {
            toast.style.display = '';
            toast.classList.remove('show');
        }
        if (this.rootRef.el) {
            const checkboxes = this.rootRef.el.querySelectorAll('.product_check_box');
            checkboxes.forEach((cb) => {
                cb.checked = false;
            });
        }
    }

    async _openWizardAction(name, resModel) {
        return this.actionService.doAction(
            {
                type: 'ir.actions.act_window',
                name: name,
                res_model: resModel,
                view_mode: 'form',
                views: [[false, 'form']],
                target: 'new',
                context: {
                    default_product_ids: this.state.products_selected,
                },
            },
            {
                onClose: async () => {
                    this._resetSelection();
                    await this.model.load();
                },
            }
        );
    }

    _onChangeCategory() {
        // Function for changing category of selected products
        return this._openWizardAction('Change Category', 'product.category.change');
    }

    _onCustLeadTimeProducts() {
        // Function for changing Customer Lead Time of selected products
        return this._openWizardAction('Change Customer Lead Time', 'product.customer.lead.time');
    }

    _onArchiveProducts() {
        // Function for archiving selected products
        return this._openWizardAction('Archive Product', 'product.archive');
    }

    _onUpdatePrice() {
        // Function for updating price of selected products
        return this._openWizardAction('Update Price', 'product.update.price');
    }

    _onAddVendor() {
        // Function for adding vendor to selected products
        return this._openWizardAction('Add Vendor', 'product.add.vendor');
    }

    _onMakeSalable() {
        // Function for making selected products salable
        return this._openWizardAction('Make Products Salable', 'product.make.salable');
    }

    _onMakePurchasable() {
        // Function for making selected products purchasable
        return this._openWizardAction('Make Products Purchasable', 'product.make.purchasable');
    }

    _onDeleteProducts() {
        // Function for deleting selected products
        return this._openWizardAction('Delete Product', 'product.delete');
    }

    _onPublishProducts() {
        // Function for publishing selected products on website
        return this._openWizardAction('Publish On Website', 'product.publish');
    }

    _onAlternativeProducts() {
        // Function for adding alternative products to selected products
        return this._openWizardAction('Add Alternative Product', 'product.alternative');
    }

    _onAccessoryProducts() {
        // Function for adding accessory products to selected products
        return this._openWizardAction('Add Accessory Product', 'product.accessory');
    }

    _onOptionalProducts() {
        // Function for adding optional products to selected products
        return this._openWizardAction('Add Optional Product', 'product.optional');
    }

    _onEditInvoicePolicyProducts() {
        // Function for editing invoice policy of selected products
        return this._openWizardAction('Edit Invoice Policy', 'product.invoice');
    }

    _onAddCustomerTaxProducts() {
        // Function for changing customer tax of selected products
        return this._openWizardAction('Change Customer Tax', 'product.customer.tax');
    }

    _onAddVendorTaxProducts() {
        // Function for changing vendor tax of selected products
        return this._openWizardAction('Change Vendor Tax', 'product.vendor.tax');
    }

    _onWebCategChangeProducts() {
        // Function for changing website category of selected products
        return this._openWizardAction('Change Category On Website', 'product.category.website');
    }

    _onAddAttributeProducts() {
        // Function for adding attributes & variants to selected products
        return this._openWizardAction('Add Product Attributes', 'product.add.attribute');
    }

    _onChangeTrackingProducts() {
        // Function for changing tracking of selected products
        return this._openWizardAction('Change Product Tracking', 'product.change.tracking');
    }

    _onChangeProductionLocation() {
        // Function for changing production location of selected products
        return this._openWizardAction('Change Production Location', 'product.production.location');
    }

    _onChangeInventoryLocation() {
        // Function for changing inventory location of selected products
        return this._openWizardAction('Change Inventory Location', 'product.inventory.location');
    }
}

const ProductKanbanView = {
    ...kanbanView,
    Controller: KanbanButton,
};

registry.category("views").add("product_management_kanban_view", ProductKanbanView);

patch(FormController.prototype, {
    async save() {
        const saved = await super.save(...arguments);
        const currentModel = this.props.resModel || (this.model && this.model.root && this.model.root.resModel);
        if (saved && (currentModel === "res.users" || currentModel === "res.config.settings")) {
            if (this.env.services.menu && this.env.services.menu.reload) {
                try {
                    await this.env.services.menu.reload();
                } catch {
                    // Suppress menu reload errors
                }
            }
        }
        return saved;
    },
});
