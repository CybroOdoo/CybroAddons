odoo.define('pos_product_creation',function(require) {

var gui = require('point_of_sale.gui');
var chrome = require('point_of_sale.chrome');
var PopupWidget = require('point_of_sale.popups');
var popups = require('point_of_sale.popups');
var core = require('web.core');
var models = require('point_of_sale.models');
var rpc = require('web.rpc');
var QWeb = core.qweb;
var _t = core._t;
models.load_models({
        model:  'product.category',
        fields: ['name'],
        loaded: function(self,categories){
            self.categories = categories;
        },
    });

chrome.OrderSelectorWidget.include({
    renderElement: function(){
        var self = this;
        this._super();
        var categ = [];
        var unit = [];
        for (var i in self.pos.categories){
            categ.push(self.pos.categories[i].name);
        }
        for (var i in self.pos.units){
            unit.push(self.pos.units[i].name);
        }
        this.$('.add-product').click(function(event){
            self.gui.show_popup('product_create',{
                'category': categ,
                'units':unit,
            });
        });
    },
});
var ProductCreationWidget = PopupWidget.extend({
    template: 'ProductCreationWidget',
    init: function(parent, args) {
        this._super(parent, args);
        this.options = {};
        this.category = [];
        this.units = [];
    },
    events: {
        'click .button.cancel':  'click_cancel',
        'click .button.confirm': 'click_confirm',
    },
    show: function(options){
        options = options || {};
        this._super(options);
        this.category = options.category;
        this.units = options.units;
        this.renderElement();
        this.$('.name').focus();
    },
    click_confirm: function(){
        var self = this;
        var name = this.$('.name').val();
        var type = this.$('.type').val();
        var category = this.$('.category').val();
        var unit = this.$('.uom').val();
        var price = this.$('.price').val();
        if(!name || !price) {
            alert("Please fill Name & price for the Product!")
        }
        else {
             var product_vals = {
                'name': name,
                'type': type,
                'category': category,
                'price': price,
                'unit': unit
            };
            rpc.query({
                    model: 'product.product',
                    method: 'create_product_pos',
                    args: [product_vals],
                }).then(function (products){
                    self.pos.db.add_products(_.map([products], function (product) {
                        product.categ = _.findWhere(self.pos.product_categories, {'id': product.categ_id[0]});
                        return new models.Product({}, product);
                    }));
                });
            this.gui.close_popup();
        }
    },
    click_cancel: function(){
        this.gui.close_popup();
        if (this.options.cancel) {
            this.options.cancel.call(this);
        }
    },
});
gui.define_popup({name:'product_create', widget: ProductCreationWidget});

});