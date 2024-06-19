odoo.define('pos_restaurant_web_menu.web_menu', function (require) {
"use strict";
    /**
        * The purpose of this module is to add the PosRestaurantWebMenu in the public
        widget registries.
    */
    var PublicWidget = require('web.public.widget');
    var rpc = require('web.rpc');
    var core = require('web.core');
    var qweb = core.qweb;
    var count=0;
    var cart_item = [];
    var PosWebMenu = PublicWidget.Widget.extend({
        selector:'.pos_web_menu_container',
        events: {
            'click .view_product_list': '_view_product_page',
            'click .add_to_cart_pos': '_onClick',
            'click .o_pos_web_menu_button': '_view_cart',
            'click .pos_web_order': '_make_an_order',
            'click .button_back': 'back'
        },
        //   Back button for pos web menu
        back: function(ev){
            this.$el.find('.pos_web_main').show()
            this.$el.find('.pos_web_cart').show()
        },
        //    Clicked Product will be added to the cart as table
        _onClick: function (ev) {
            var id = this.$(ev.currentTarget).attr("data-value");
            var self = this;
            var product_id = parseInt(id)
            var amount = 0
            rpc.query({
                route: '/product/pos_cart',
                params: {
                    product_id: parseInt(product_id)
                },
            }).then(function (data) {
                amount = data['lst_price']
                cart_item.push(data)
                self.$el.find("tbody").append("<tr id='demo'><td><span>"+data['display_name']+"</span></td><td><span>"+data['currency']+ amount+"</span></td><td><input type='text' width='30%' class='form-control' placeholder='Add internal note..' /></td><tr>");
            });
            self.$el.find(".cart_products").text((cart_item.length+1));
        },
        //  view cart for POS
        _view_cart: function (ev){
            this.$el.find(".pos_web_main").hide()
            this.$el.find(".pos_web_cart").show()
        },
        // Create an order or add product to existing order in drafted state if exists
        _make_an_order: function (ev) {
            var inputs, index, note=[];
            var self = this;
            var config_id = this.$('.o_pos_web_menu_button').attr("data-value")
            var table = this.$('#tables_id').val()
            var customer = this.$('#customer_id').val()
            inputs = document.getElementsByTagName('input');
            for (index = 0; index < inputs.length; ++index) {
            // deal with inputs[index] element.
                note.push(inputs[index].value)
            }
            // Internal note  added to cart_item array
            $.each(cart_item, function(index, obj) {
                obj.cust_note = note[index];
            });
            // Call a method in pos_config to create order
            rpc.query({
                model: 'pos.config',
                method: 'create_order_from_web',
                args:[parseInt(config_id),cart_item,parseInt(table),parseInt(customer)]
            }).then(function(data){
                if(data === "False") {
                    self.$el.find("#alert").show()
                    self.$el.find("#alert").text("Order already exists for this table. Please select a different table or try again later.")
                }
                else{
                    location.reload();
                }
            });
        },
        //    To view Product list on clicking view menu on landing page of pos web menu
        _view_product_page: function(ev){
            this.$el.find(".pos_web_front_page").hide();
            this.$el.find(".pos_web_product_page").show();
        },
    });
    PublicWidget.registry.PosWebMenu = PosWebMenu;
    return PosWebMenu;
});

