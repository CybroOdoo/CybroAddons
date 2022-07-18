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
    var rpc = require('web.rpc');
    var models = require('point_of_sale.models');


models.load_models({
    model:  'res.lang',
    fields: ['name', 'code'],
    domain: function(self){
        return [['active', '=', true]];
    },
    loaded: function(self, lang) {
            self.lang = lang;
        }

})


    class LangWidget extends PosComponent {


        constructor() {
            super(...arguments);

            this.lang_list = [];

            }

//Pushing the languages at DOM mount

        mounted(options){

            this.lang_list = this.env.pos.lang;
            this.current_lang = this.env.pos.user.lang;
            this.render();

        }

//Click events

    click_confirm(){
        var self = this;
        var lang = parseInt($('.lang').val());
            rpc.query({
                model: 'pos.order',
                method: 'switch_lang',
                args: [lang],

            }).then(val => {
                this.env.pos.do_action({
                type: "ir.actions.client",
                tag: 'reload',
            });
            })
        this.trigger('close-popup');
        return;

    }
    click_cancel(){
        this.trigger('close-popup');


    }

    }

    LangWidget.template = 'LangWidget';
    LangWidget.defaultProps = {
        confirmText: 'Return',
        cancelText: 'Cancel',
        title: 'Confirm ?',
        body: '',
    };
    Registries.Component.add(LangWidget);
    return LangWidget;
});

