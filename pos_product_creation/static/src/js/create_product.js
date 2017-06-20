odoo.define('pos_product_creation',function(require) {

var gui = require('point_of_sale.gui');
var chrome = require('point_of_sale.chrome');
var PosBaseWidget = require('point_of_sale.BaseWidget');
var popups = require('point_of_sale.popups');
var core = require('web.core');
var models = require('point_of_sale.models');
var Model = require('web.DataModel');
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
                'confirm': function(value) {
                },
            });
        });
    },
});
var ProductCreationWidget = PosBaseWidget.extend({
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
    close: function(){
        if (this.pos.barcode_reader) {
            this.pos.barcode_reader.restore_callbacks();
        }
    },
    click_confirm: function(){
        var self = this;
        var name = this.$('.name').val();
        var type = this.$('.type').val();
        var category = this.$('.category').val();
        var unit = this.$('.uom').val();
        var price = this.$('.price').val();
        if(isNaN(price) || !price) {
            alert("Please check the price !")
        }
        else {
             var product_vals = {
                'name': name,
                'type': type,
                'category': category,
                'price': price,
                'unit': unit
            };
            new Model('product.product').call('create_product_pos',[1, product_vals]).then(function(product){
                    self.pos.db.add_products([product]);
                    console.log(self)
                });
            console.log(product_vals)
            this.gui.close_popup();
            if( this.options.confirm ){
                this.options.confirm.call(this,name);
            }
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