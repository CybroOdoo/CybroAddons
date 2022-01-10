odoo.define('product_multi_uom_pos.multi_uom_widget',function(require) {
    "use strict";

var gui = require('point_of_sale.Gui');
var core = require('web.core');
var QWeb = core.qweb;

    const NumberBuffer = require('point_of_sale.NumberBuffer');
    const { onChangeOrder, useBarcodeReader } = require('point_of_sale.custom_hooks');
    const PosComponent = require('point_of_sale.PosComponent');
    const Registries = require('point_of_sale.Registries');
    const ProductScreen = require('point_of_sale.ProductScreen');
    const { useListener } = require('web.custom_hooks');
    const { useState, useRef } = owl.hooks;




    class MultiUomWidget extends PosComponent {


        constructor() {
            super(...arguments);

            this.options = {};
            this.uom_list = [];

            }

        mounted(options){

            var current_uom = this.env.pos.units_by_id[this.props.options.uom_list[0]];
            var uom_list = this.env.pos.units_by_id;
            var uom_by_category = this.get_units_by_category(uom_list, current_uom.category_id);
            this.uom_list = uom_by_category;
            this.current_uom = this.props.options.uom_list[0];
            this.render();

        }

 get_units_by_category(uom_list, categ_id){
        var uom_by_categ = []
        for (var uom in uom_list){
            if(uom_list[uom].category_id[0] == categ_id[0]){
                uom_by_categ.push(uom_list[uom]);
            }
        }
        return uom_by_categ;
    }
    /*Find the base price(price of the product for reference unit)*/
    find_reference_unit_price(product, product_uom){
        if(product_uom.uom_type == 'reference'){
            return product.lst_price;
        }
        else if(product_uom.uom_type == 'smaller'){
           return (product.lst_price * product_uom.factor);
        }
        else if(product_uom.uom_type == 'bigger'){
           return (product.lst_price / product_uom.factor_inv);
        }
    }
    /*finds the latest price for the product based on the new uom selected*/
    get_latest_price(uom, product){
        var uom_by_category = this.get_units_by_category(this.env.pos.units_by_id, uom.category_id);
        var product_uom = this.env.pos.units_by_id[product.uom_id[0]];
        var ref_price = this.find_reference_unit_price(product, product_uom);
        var ref_price = product.lst_price;
        var ref_unit = null;
        for (var i in uom_by_category){
            if(uom_by_category[i].uom_type == 'reference'){
                ref_unit = uom_by_category[i];
                break;
            }
        }
        if(ref_unit){
            if(uom.uom_type == 'bigger'){
                          console.log("bigggg");
                          console.log("ref_price * uom.factor_inv",ref_price * uom.factor_inv);

                return (ref_price * uom.factor_inv);
            }
            else if(uom.uom_type == 'smaller'){
                          console.log("smalll");
                          console.log("small",(ref_price / uom.factor_inv));

                return (ref_price / uom.factor);
            }
            else if(uom.uom_type == 'reference'){
                          console.log("refernce");
                            console.log("ref_price",ref_price);
                return ref_price;
            }
        }
        return product.lst_price;
    }


    click_confirm(){
        var self = this;
        var uom = parseInt($('.uom').val());
        var order = this.env.pos.get_order();
        var orderline = order.get_selected_orderline();
        var selected_uom = this.env.pos.units_by_id[uom];
        orderline.uom_id = [];
        orderline.uom_id[0] = uom;
        orderline.uom_id[1] = selected_uom.display_name;

        /*Updating the orderlines*/
        order.remove_orderline(orderline);
        order.add_orderline(orderline);
        var latest_price = this.get_latest_price(selected_uom, orderline.product);
        order.get_selected_orderline().set_unit_price(latest_price);
        orderline.lst_price = latest_price;

        this.trigger('close-popup');
        return;

    }
    click_cancel(){
        this.trigger('close-popup');
    }

    }


    MultiUomWidget.template = 'MultiUomWidget';
    MultiUomWidget.defaultProps = {
        confirmText: 'Return',
        cancelText: 'Cancel',
        title: 'Confirm ?',
        body: '',
    };
    Registries.Component.add(MultiUomWidget);
    return MultiUomWidget;
});

