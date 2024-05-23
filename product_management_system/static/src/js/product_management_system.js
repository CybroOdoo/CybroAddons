/** @odoo-module **/

var KanbanController = require('web.KanbanController');
var KanbanView = require('web.KanbanView');
var viewRegistry = require('web.view_registry');
var products_selected = [];

var KanbanButton = KanbanController.extend({
// Extending KanbanController and Creating buttons and its functions
    buttons_template: 'button_in_kanban.button',
    events: _.extend({}, KanbanController.prototype.events, {
        'click .product_check_box': '_onSelectDocs',
        'click .on_change_category': '_onChangeCategory',
        'click .on_customer_lead_time_products': '_onCustLeadTimeProducts',
        'click .on_archive_products': '_onArchiveProducts',
        'click .on_update_price': '_onUpdatePrice',
        'click .on_add_vendor': '_onAddVendor',
        'click .on_make_salable': '_onMakeSalable',
        'click .on_make_purchasable': '_onMakePurchasable',
        'click .on_delete_products': '_onDeleteProducts',
        'click .on_alternative_products': '_onAlternativeProducts',
        'click .on_accessory_products': '_onAccessoryProducts',
        'click .on_optional_products': '_onOptionalProducts',
        'click .on_edit_invoice_policy_products': '_onEditInvoicePolicyProducts',
        'click .on_add_cust_tax_products': '_onAddCustomerTaxProducts',
        'click .on_add_vendor_tax_products': '_onAddVendorTaxProducts',
        'click .on_publish_products': '_onPublishProducts',
        'click .on_change_web_category_products': '_onWebCategChangeProducts',
        'click .on_add_attribute_products': '_onAddAttributeProducts',
        'click .on_change_tracking_products': '_onChangeTrackingProducts',
        'click .change_production_location_products': '_onChangeProductionLocation',
        'click .change_inventory_location_products': '_onChangeInventoryLocation',
    }),

    start: function(){
        return this._super().then(function() {})
    },

    _onSelectDocs: function(ev){
        // Function for selecting products and appending in the products_selected list
        var toast = $('.toast')
        var checked = $(ev.target).is(':checked');
        var record_id =parseInt($(ev.target).data('id'));
        if (checked){
            toast.addClass('show');
            toast.css("display","inline");
            products_selected.push(record_id);
        }
        else{
            let index = products_selected.indexOf(record_id);
            products_selected.splice(index, 1)
            if ( products_selected.length == 0){
                toast.css("display","");
                toast.removeClass('show');
            }
        }
    },

    _onChangeCategory: function(ev){
    //    Function for changing category of selected products
        this.do_action({
            type: 'ir.actions.act_window',
            name: 'Change Category',
            res_model: 'product.category.change',
            view_mode: 'form',
            views: [[false, 'form']],
            target: 'new',
            context: {
                'default_product_ids': products_selected,
            },
        });
    },

    _onCustLeadTimeProducts: function(ev){
    //    Function for changing Customer Lead Time of selected products
        this.do_action({
            type: 'ir.actions.act_window',
            name: 'Change Customer Lead Time',
            res_model: 'product.customer.lead.time',
            view_mode: 'form',
            views: [[false, 'form']],
            target: 'new',
            context: {
                'default_product_ids': products_selected,
            },
        });
    },

    _onArchiveProducts: function(ev){
    //    Function for changing Archive Product of selected products
        this.do_action({
            type: 'ir.actions.act_window',
            name: 'Archive Product',
            res_model: 'product.archive',
            view_mode: 'form',
            views: [[false, 'form']],
            target: 'new',
            context: {
                'default_product_ids': products_selected,
            },
        });
    },

    _onUpdatePrice: function(ev){
    //    Function for changing Update Price of selected products
        this.do_action({
            type: 'ir.actions.act_window',
            name: 'Update Price',
            res_model: 'product.update.price',
            view_mode: 'form',
            views: [[false, 'form']],
            target: 'new',
            context: {
                'default_product_ids': products_selected,
            },
        });
    },

    _onAddVendor: function(ev){
    //    Function for changing Add Vendor of selected products
        this.do_action({
            type: 'ir.actions.act_window',
            name: 'Add Vendor',
            res_model: 'product.add.vendor',
            view_mode: 'form',
            views: [[false, 'form']],
            target: 'new',
            context: {
                'default_product_ids': products_selected,
            },
        });
    },

    _onMakeSalable: function(ev){
        //    Function for Make Salable of selected products
        this.do_action({
            type: 'ir.actions.act_window',
            name: 'Make Products Salable',
            res_model: 'product.make.salable',
            view_mode: 'form',
            views: [[false, 'form']],
            target: 'new',
            context: {
                'default_product_ids': products_selected,
            },
        });
    },

    _onMakePurchasable: function(ev){
    //    Function for Make Purchasable of selected products
        this.do_action({
            type: 'ir.actions.act_window',
            name: 'Make Products Purchasable',
            res_model: 'product.make.purchasable',
            view_mode: 'form',
            views: [[false, 'form']],
            target: 'new',
            context: {
                'default_product_ids': products_selected,
            },
        });
    },

    _onDeleteProducts: function(ev){
    //    Function for Deleting the selected products
        this.do_action({
            type: 'ir.actions.act_window',
            name: 'Delete Product',
            res_model: 'product.delete',
            view_mode: 'form',
            views: [[false, 'form']],
            target: 'new',
            context: {
                'default_product_ids': products_selected,
            },
        });
    },

    _onPublishProducts : function(ev){
    //    Function for Publish On Website of selected products
        this.do_action({
            type: 'ir.actions.act_window',
            name: 'Publish On Website',
            res_model: 'product.publish',
            view_mode: 'form',
            views: [[false, 'form']],
            target: 'new',
            context: {
                'default_product_ids': products_selected,
            },
        });
    },

    _onAlternativeProducts: function(ev){
    //    Function for Adding Alternative Product of selected products
        this.do_action({
            type: 'ir.actions.act_window',
            name: 'Add Alternative Product',
            res_model: 'product.alternative',
            view_mode: 'form',
            views: [[false, 'form']],
            target: 'new',
            context: {
                'default_product_ids': products_selected,
            },
        });
    },

    _onAccessoryProducts: function(ev){
    //    Function for Adding Accessory Product of selected products
        this.do_action({
            type: 'ir.actions.act_window',
            name: 'Add Accessory Product',
            res_model: 'product.accessory',
            view_mode: 'form',
            views: [[false, 'form']],
            target: 'new',
            context: {
                'default_product_ids': products_selected,
            },
        });
    },

    _onOptionalProducts: function(ev){
    //    Function for Adding Optional Product of selected products
        this.do_action({
            type: 'ir.actions.act_window',
            name: 'Add Optional Product',
            res_model: 'product.optional',
            view_mode: 'form',
            views: [[false, 'form']],
            target: 'new',
            context: {
                'default_product_ids': products_selected,
            },
        });
    },

    _onEditInvoicePolicyProducts:function(ev){
    //    Function for Editing Invoice Policy of selected products
        this.do_action({
            type: 'ir.actions.act_window',
            name: 'Edit Invoice Policy',
            res_model: 'product.invoice',
            view_mode: 'form',
            views: [[false, 'form']],
            target: 'new',
            context: {
                'default_product_ids': products_selected,
            },
        });
    },

    _onAddCustomerTaxProducts: function(ev){
    //    Function for Changing Customer Tax of selected products
        this.do_action({
            type: 'ir.actions.act_window',
            name: 'Change Customer Tax',
            res_model: 'product.customer.tax',
            view_mode: 'form',
            views: [[false, 'form']],
            target: 'new',
            context: {
                'default_product_ids': products_selected,
            },
        });
    },

    _onAddVendorTaxProducts: function(ev){
    //    Function for Changing Vendor Tax of selected products
        this.do_action({
            type: 'ir.actions.act_window',
            name: 'Change Vendor Tax',
            res_model: 'product.vendor.tax',
            view_mode: 'form',
            views: [[false, 'form']],
            target: 'new',
            context: {
                'default_product_ids': products_selected,
            },
        });
    },

    _onWebCategChangeProducts: function(ev){
    //    Function for Changing Category On Website of selected products
        this.do_action({
            type: 'ir.actions.act_window',
            name: 'Change Category On Website',
            res_model: 'product.category.website',
            view_mode: 'form',
            views: [[false, 'form']],
            target: 'new',
            context: {
                'default_product_ids': products_selected,
            },
        });
    },
    _onAddAttributeProducts : function(ev){
    //    Function for Adding Product Attributes of selected products
        this.do_action({
            type: 'ir.actions.act_window',
            name: 'Add Product Attributes',
            res_model: 'product.add.attribute',
            view_mode: 'form',
            views: [[false, 'form']],
            target: 'new',
            context: {
                'default_product_ids': products_selected,
            },
        });
    },

    _onChangeTrackingProducts: function(ev){
    //    Function for Changing Product Tracking of selected products
        this.do_action({
            type: 'ir.actions.act_window',
            name: 'Change Product Tracking',
            res_model: 'product.change.tracking',
            view_mode: 'form',
            views: [[false, 'form']],
            target: 'new',
            context: {
                'default_product_ids': products_selected,
            },
        });
    },

    _onChangeProductionLocation: function(ev){
    //    Function for Changing Production Location of selected products
        this.do_action({
            type: 'ir.actions.act_window',
            name: 'Change Production Location',
            res_model: 'product.production.location',
            view_mode: 'form',
            views: [[false, 'form']],
            target: 'new',
            context: {
                'default_product_ids': products_selected,
            },
        });
    },

    _onChangeInventoryLocation: function(ev){
    //    Function for Changing Inventory Location of selected products
        this.do_action({
            type: 'ir.actions.act_window',
            name: 'Change Inventory Location',
            res_model: 'product.inventory.location',
            view_mode: 'form',
            views: [[false, 'form']],
            target: 'new',
            context: {
                'default_product_ids': products_selected,
            },
        });
    },
});

var ProductKanbanView = KanbanView.extend({
   config: _.extend({}, KanbanView.prototype.config, {
       Controller: KanbanButton,
   }),
});
viewRegistry.add('product_management_kanban_view', ProductKanbanView);
