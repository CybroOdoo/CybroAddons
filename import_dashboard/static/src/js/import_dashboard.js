odoo.define('import_dashboard.dashboard', function(require) {
    "use strict";
    var AbstractAction = require('web.AbstractAction');
    var core = require('web.core');
    var check_bill_of_material = ''
    var check_pos = ''
    var check_attendance = ''
    var check_payment = ''
    var check_task = ''
    var check_sale = ''
    var check_purchase = ''
    var check_product = ''
    var check_partner = ''
    var check_invoice = ''
    var check_pricelist = ''
    var check_vendor_pricelist = ''
    var ImportDashBoard = AbstractAction.extend({
        template: 'imp_dash',
        events: {
            'click .import_sale': 'import_sale',
            'click .import_purchase': 'import_purchase',
            'click .import_invoice': 'import_invoice',
            'click .import_partner': 'import_partner',
            'click .import_product_pricelist': 'import_product_pricelist',
            'click .import_bill_of_material': 'import_bill_of_material',
            'click .import_product_template': 'import_product_template',
            'click .import_vendor_pricelist': 'import_vendor_pricelist',
            'click .import_pos': 'import_pos',
            'click .import_attendance': 'import_attendance',
            'click .import_payment': 'import_payment',
            'click .import_task': 'import_task',
        },
        willStart: function() {
            //For enabling the corresponding boolean field for modules in the dashboard
            var self = this;
            return this._super()
                .then(function() {
                    var def0 = self._rpc({
                        model: 'ir.config_parameter',
                        method: 'check_user_group'
                    }).then(function(result) {
                        if (result['bill_of_material']) {
                            self.check_bill_of_material = true;
                        } else {
                            self.check_bill_of_material = false;
                        }
                        if (result['pos']) {
                            self.check_pos = true;
                        } else {
                            self.check_pos = false;
                        }
                        if (result['import_attendance']) {
                            self.check_attendance = true;
                        } else {
                            self.check_attendance = false;
                        }
                        if (result['import_payment']) {
                            self.check_payment = true;
                        } else {
                            self.check_payment = false;
                        }
                        if (result['import_task']) {
                            self.check_task = true;
                        } else {
                            self.check_task = false;
                        }
                        if (result['import_sale']) {
                            self.check_sale = true;
                        } else {
                            self.check_sale = false;
                        }
                        if (result['import_purchase']) {
                            self.check_purchase = true;
                        } else {
                            self.check_purchase = false;
                        }
                        if (result['import_product_template']) {
                            self.check_product = true;
                        } else {
                            self.check_product = false;
                        }
                        if (result['import_partner']) {
                            self.check_partner = true;
                        } else {
                            self.check_partner = false;
                        }
                        if (result['import_invoice']) {
                            self.check_invoice = true;
                        } else {
                            self.check_invoice = false;
                        }
                        if (result['import_pricelist']) {
                            self.check_pricelist = true;
                        } else {
                            self.check_pricelist = false;
                        }
                        if (result['import_vendor_pricelist']) {
                            self.check_vendor_pricelist = true;
                        } else {
                            self.check_vendor_pricelist = false;
                        }
                    });
                    return $.when(def0);
                });
        },
        start: function() {
            //super the start function for calling the check_data() function
            var self = this;
            return this._super().then(function() {
                self.check_data();
            });
        },
        check_data: function() {
            //For showing the corresponding tiles in the dashboard
            var self = this;
            if (self.check_bill_of_material == true) {
                self.$("card_bill_of_material").show();
                self.$('.start_msg').hide();
            } else {
                self.$("#card_bill_of_material").hide();
            }
            if (self.check_pos == true) {
                self.$("#card_pos").show();
                self.$('.start_msg').hide();
            } else {
                self.$("#card_pos").hide();
            }
            if (self.check_attendance == true) {
                self.$("#card_attendance").show();
                self.$('.start_msg').hide();
            } else {
                self.$("#card_attendance").hide();
            }
            if (self.check_payment == true) {
                self.$("#card_payment").show();
                self.$('.start_msg').hide();
            } else {
                self.$("#card_payment").hide();
            }
            if (self.check_task == true) {
                self.$("#card_task").show();
                self.$('.start_msg').hide();
            } else {
                self.$("#card_task").hide();
            }
            if (self.check_sale == true) {
                self.$("#card_sale").show();
                self.$('.start_msg').hide();
            } else {
                self.$("#card_sale").hide();
            }
            if (self.check_purchase == true) {
                self.$("#card_purchase").show();
                self.$('.start_msg').hide();
            } else {
                self.$("#card_purchase").hide();
            }
            if (self.check_product == true) {
                self.$("#card_product").show();
                self.$('.start_msg').hide();
            } else {
                self.$("#card_product").hide();
            }
            if (self.check_partner == true) {
                self.$("#card_partner").show();
                self.$('.start_msg').hide();
            } else {
                self.$("#card_partner").hide();
            }
            if (self.check_invoice == true) {
                self.$("#card_invoice").show();
                self.$('.start_msg').hide();
            } else {
                self.$("#card_invoice").hide();
            }
            if (self.check_pricelist == true) {
                self.$("#card_pricelist").show();
                self.$('.start_msg').hide();
            } else {
                self.$("#card_pricelist").hide();
            }
            if (self.check_vendor_pricelist == true) {
                self.$("#card_vendor_pricelist").show();
                self.$('.start_msg').hide();
            } else {
                self.$("#card_vendor_pricelist").hide();
            }
        },
        import_sale: function(e) {
            //For loading the import of sales order form view
            var self = this;
            this.do_action({
                name: "Import Sale Order",
                type: 'ir.actions.act_window',
                res_model: 'import.sale.order',
                view_mode: 'form',
                views: [[false, 'form']],
                target: 'new',
            })
        },
        import_purchase: function(e) {
            //For loading the import of purchase order form view
            this.do_action({
                name: "Import Purchase Order",
                type: 'ir.actions.act_window',
                res_model: 'import.purchase.order',
                view_mode: 'form',
                views: [[false, 'form']],
                target: 'new',
            })
        },
        import_invoice: function(e) {
            //For loading the import of invoice form view
            this.do_action({
                name: "Import Invoice",
                type: 'ir.actions.act_window',
                res_model: 'import.invoice',
                view_mode: 'form',
                views: [[false, 'form']],
                target: 'new',
            })
        },
        import_partner: function(e) {
            //For loading the import of partner form view
            this.do_action({
                name: "Import Partner",
                type: 'ir.actions.act_window',
                res_model: 'import.partner',
                view_mode: 'form',
                views: [[false, 'form']],
                target: 'new',
            })
        },
        import_product_pricelist: function(e) {
            //For loading the import of product price-list form view
            this.do_action({
                name: "Import Product Pricelist",
                type: 'ir.actions.act_window',
                res_model: 'import.product.pricelist',
                view_mode: 'form',
                views: [[false, 'form']],
                target: 'new',
            })
        },
        import_bill_of_material: function(e) {
            //For loading the import of BOM form view
            var self = this;
            this.do_action({
                name: "Import Bill of Material",
                type: 'ir.actions.act_window',
                res_model: 'import.bill.of.material',
                view_mode: 'form',
                views: [[false, 'form']],
                target: 'new',
            })
        },
        import_product_template: function(e) {
            //For loading the import of product template form view
            var self = this;
            this.do_action({
                name: "Import Product",
                type: 'ir.actions.act_window',
                res_model: 'import.product.template',
                view_mode: 'form',
                views: [[false, 'form']],
                target: 'new',
            })
        },
        import_vendor_pricelist: function(e) {
            //For loading the import of vendor price-list form view
            var self = this;
            this.do_action({
                name: "Import Vendor Pricelist",
                type: 'ir.actions.act_window',
                res_model: 'import.vendor.pricelist',
                view_mode: 'form',
                views: [[false, 'form']],
                target: 'new',
            })
        },
        import_pos: function(e) {
            //For loading the import of pos orders form view
            var self = this;
            this.do_action({
                name: "Import POS",
                type: 'ir.actions.act_window',
                res_model: 'import.pos',
                view_mode: 'form',
                views: [[false, 'form']],
                target: 'new',
            })
        },
        import_attendance: function(e) {
            //For loading the import of attendance form view
            var self = this;
            this.do_action({
                name: "Import Attendance",
                type: 'ir.actions.act_window',
                res_model: 'import.attendance',
                view_mode: 'form',
                views: [[false, 'form']],
                target: 'new',
            })
        },
        import_payment: function(e) {
            //For loading the import of payments form view
            var self = this;
            this.do_action({
                name: "Import Payment",
                type: 'ir.actions.act_window',
                res_model: 'import.payment',
                view_mode: 'form',
                views: [[false, 'form']],
                target: 'new',
            })
        },
        import_task: function(e) {
            //For loading the import of task form view
            var self = this;
            this.do_action({
                name: "Import Task",
                type: 'ir.actions.act_window',
                res_model: 'import.task',
                view_mode: 'form',
                views: [[false, 'form']],
                target: 'new',
            })
        },
    })
    core.action_registry.add('import_dashboard_tag', ImportDashBoard);
    return ImportDashBoard;
});
