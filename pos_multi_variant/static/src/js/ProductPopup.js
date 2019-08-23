odoo.define('pos_multi_variant.ProductPopup', function (require)
{   "use strict";

    var PosBaseWidget = require('point_of_sale.BaseWidget');
    var gui = require('point_of_sale.gui');
    var models = require('point_of_sale.models');
    var core = require('web.core');
    var screens = require('point_of_sale.screens');
    var PopupWidget = require('point_of_sale.popups');
    var Widget = require("web.Widget");
    var QWeb = core.qweb;
    var rpc = require('web.rpc');
    var _t  = require('web.core')._t;

    models.load_models([
    {   model: 'variants.tree',
        fields: ["variants.tree", "pos_active", "value", "attribute", "variants_id", "extra_price"],
        loaded: function(self, variants_tree)
        {   self.variant_tree = variants_tree;
            _.each(variants_tree, function(item)
            {   self.item = item;
            });
        }
    },{    model: 'product.attribute.value',
            fields: ["id", "name"],
            loaded: function(self,values)
            {   self.values = values;
            }
      }]);

    var super_models = models.PosModel.prototype.models;
    models.load_fields('product.product','pos_variants');
    models.load_fields('product.product','variant_line_ids');

    var _super_orderline = models.Orderline.prototype;
    models.Orderline = models.Orderline.extend
    ({   initialize: function(attr, options)
        {   _super_orderline.initialize.call(this,attr,options);
            this.product_variants = this.product_variants || [];
        },
        init_from_JSON: function(json)
        {   _super_orderline.init_from_JSON.apply(this,arguments);
            this.product_variants = json.product_variants || [];
        },
        export_as_JSON: function ()
        {   var json = _super_orderline.export_as_JSON.apply(this, arguments);
            json.product_variants = this.product_variants || [];
            return json;
        },
    });

    var ProductPopUp = PopupWidget.extend
    ({   template: 'ProductPopUp',

        init: function(parent, options)
        {   this._super(parent, options);
            this.options = {};
            this.pos_reference = "";
        },

        show: function(options)
        {   var self =this;
            this._super(options);
            this.render_list(options);
        },

        events:
        {   'click .button.cancel':  'click_cancel',
            'click .button.confirm': 'click_confirm',
            'click .product': 'click_variant',
        },

        click_variant:function(e)
        {   var order = this.self.pos.get('selectedOrder')
            var self = e.currentTarget
            var action = $(self).find('.action').text();
            var categories = []

            var category = $(self).find('.action').data('category');
            $('.product-img').find('.variant-selected').each(function ()
            {   if($(this).data('category') ==  category) // if so
                {   $(this).text("").removeClass('variant-selected');
                    $(self).find('.action').text("Selected").addClass('variant-selected');
                }
            });
            $(self).find('.action').text("Selected").addClass('variant-selected');
            var add = $(self).find('.extra-price').text().substr(1).slice(0, -2);
            var type = $(self).find('.variants').text();
            $(self).find('.variant-selected').attr('data-price', add);
            $(self).find('.variant-selected').attr('data-type', type);
        },

        render_list:function(options)
        {   this.list = options.list
            this.image_url    = options.image_url
            this.pos_reference = options.data
            this.variant_values = options.values
            this.self = options.self
            var AddError = "variants are not added";
            var ActiveError = "No active variants "
            var NotActive = 0;
            var AttributeNumbers = []
            var pushed = []

            for (var i = 0; i < this.list.length; i++)
            {   if(this.list[i].pos_active == false)
                {   NotActive += 1
                }
                if(this.list[i].pos_active == true)
                {   if (!pushed.includes(this.list[i].attribute[0]))
                    {   var temp = {};
                        temp.id = this.list[i].attribute[0];
                        temp.name = this.list[i].attribute[1]
                        pushed.push(this.list[i].attribute[0])
                        AttributeNumbers.push(temp)
                    }
                }
                if(this.list.length == NotActive)
                {   $("#notify").append(ActiveError);
                }
            }
            var tag = "<div class='"+i+"'>";
            for ( var i in AttributeNumbers)
            {   tag += "<h2 class='tag'>"+AttributeNumbers[i].name+"</h2>";
                for (var attr = 0; attr < this.list.length; attr++)
                {   if (AttributeNumbers[i].id == this.list[attr].attribute[0])
                    {   var values = this.list[attr].value.length
                        for(var j = 0; j < values; j++)
                        {   if(this.list[attr].extra_price)
                            {   var price = '+'+this.format_currency(this.list[attr].extra_price)}
                            else
                            {   var price = '+'+this.format_currency(0.00)}
                            for(var k=0; k < this.variant_values.length; k++)
                            {   if((this.variant_values[k].id == this.list[attr].value[j]) && this.list[attr].pos_active == true)
                                {   var rows ="<article class='product'>" +
                                    "<div class='product-img'>"+
                                    "<img src='"+this.image_url+"'/>" +
                                    "<span class='extra-price'>"+price+"</span>"+
                                    "<h2 class='action' data-price='' data-type='' data-category='"+AttributeNumbers[i].name+""'></h2>"+
                                    "<span class='variants'>"+this.variant_values[k].name+"</span>"+
                                    "</div>"+
                                    "</article>"
                                    tag += rows
                                }
                            }
                        }
                    }
                }
            }
            tag += "</div>"
            $("#notify").append(tag);

            if(!(this.pos_reference.variant_line_ids.length>0))
            {   $("#notify").append(AddError);
            }
        },

        click_cancel: function()
        {   var order = this.self.pos.get('selectedOrder').selected_orderline.product_variants = []
            this.gui.close_popup();
        },

        click_confirm: function()
        {   var price = 0.00
            var order = this.self.pos.get_order();
            var selected_orderline = order.selected_orderline
            $('.product-img').find('.variant-selected').each(function ()
            {   price += parseFloat($(this).data('price'))
                var variant = order.selected_orderline.product_variants
                variant.push
                ({  'extra_price': $(this).data('price'),
                    'type': $(this).data('type'),
                })
            });
            selected_orderline.price_manually_set = true;
            selected_orderline.price += price
            selected_orderline.trigger('change', selected_orderline);
            this.gui.close_popup();
        }
    });
    gui.define_popup({name:'ProductSelection', widget: ProductPopUp});

    screens.ProductScreenWidget.include
    ({  click_product: function(product)
        {   var image_url = this.get_product_image(product.id);
            var self = this;
            var variant_tree = this.pos.variant_tree
            var list = []
            var values = this.pos.values
            for(var i = 0; i < variant_tree.length; i++)
            {   if(variant_tree[i].variants_id[0] == product.product_tmpl_id)
                {   list.push(variant_tree[i]); }
            }
            if(product.to_weight && this.pos.config.iface_electronic_scale)
            {   this.gui.show_screen('scale',{product: product});}
            else if(product.pos_variants)
            {   this.pos.get_order().add_product(product);
                this.gui.show_popup('ProductSelection',
                {   'title': product.display_name,
                    data: product,
                    image_url: image_url,
                    list: list,
                    values: values,
                    self: self
                });
            }
            else
            {   this.pos.get_order().add_product(product); }
        },
        get_product_image: function(product)
        {   return window.location.origin + '/web/image?model=product.product&field=image_medium&id='+product; }
    });
});
