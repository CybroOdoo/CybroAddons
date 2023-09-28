/** @odoo-module **/

    var AbstractAction = require('web.AbstractAction');
    var core = require('web.core');
    var rpc = require('web.rpc');
    var BarcodeScanner = require("@web/webclient/barcode/barcode_scanner");
    //extending abstract actions for the dashboard
    var product_detail_search_barcode_dashboard = AbstractAction.extend({
        template: 'CustomDashBoardFindProduct',
        events: {
            'keypress': '_onKeypress',
            'change': '_onChange'
        },
        //set up the dashboard template
        init: function(parent, context) {
            var self = this;
            this._super(parent, context);
            this.dashboards_templates = ['product_detail_search_template'];
        },
        //For getting the corresponding barcode of the product
        //when detect barcode scan
        _onKeypress: function(data) {
            this.typed_into = true;
        },
        //For detect the barcode scan after the keypress event and getting the
        //corresponding product details from the backend
        _onChange: function(data) {
        var self=this;
        var barcode_value = this.$("#" + data.target.id).val();
            if (this.typed_into) {
                var def1 = self._rpc({
                        model: 'product.template',
                        method: 'product_detail_search',
                        args: [[], barcode_value],
                    }).then(function(result) {
                        self.barcode_value = barcode_value;
                        if (result==false) {
                        self.product_details=false
                        }
                        else {
                        self.product_details = result
                        }
                        self.render_dashboards();
                    });
                this.typed_into = false;
            }
        },
        //Used to call the render_dashboards when the start function called
        start: function() {
            var self = this;
            this.set("title", 'Dashboard');
            return this._super().then(function() {
                self.render_dashboards();
            });
        },
        //Used to render the dashboard
        render_dashboards: function() {
            var self = this;
            _.each(this.dashboards_templates, function(template) {
                self.$('.o_pj_dashboard').html(core.qweb.render(template, {
                    widget: self
                }));
            });
        },
    });
    core.action_registry.add('product_detail_search_barcode_main_menu', product_detail_search_barcode_dashboard);
    return product_detail_search_barcode_dashboard;
