odoo.define('pos_book_order.PickupOrder',function(require){
"use strict";

    var gui = require('point_of_sale.gui');
    var chrome = require('point_of_sale.chrome');
    var core = require('web.core');
    var models = require('point_of_sale.models');
    var PosModelSuper = models.PosModel;
    var pos_screens = require('point_of_sale.screens');
    var QWeb = core.qweb;
    var _t = core._t;


    var PickupOrdersWidget = pos_screens.ScreenWidget.extend({
        template: 'PickupOrdersWidget',
        init: function(parent, options){
            this._super(parent, options);
        },
        show: function(){
            var self = this;
            this._super();
            this.renderElement();
            this.$('.cancel').click(function(){
                self.gui.show_screen('BookedOrdersWidget');
            });

            var quotations = []
             for (var i=0;i < this.pos.quotations.length ;i++){
                if (this.pos.quotations[i].pickup_date != false){
                      quotations.push(this.pos.quotations[i]);
                }
            }
            self.quotations = quotations;
            this.render_list(quotations);
            this.$('.pickup-list-contents').delegate('.pickup-line .confirm_pos_order','click',function(event){
                self.line_select(event,$(this.parentElement.parentElement),parseInt($(this.parentElement.parentElement).data('id')))
            });

        },

        render_list: function(quotations){
            var length = quotations.length
            var contents = this.$el[0].querySelector('.pickup-list-contents');
            contents.innerHTML = "";
            for(var i = 0, len = Math.min(quotations.length,1000); i < len; i++){
                var quotation    = quotations[i];
                var quotation_line_html = QWeb.render('PickupOrderLIne',{widget: this, quotation:quotations[i]});
                var quotation_line = document.createElement('tbody');
                quotation_line.innerHTML = quotation_line_html;
                quotation_line = quotation_line.childNodes[1];
                contents.appendChild(quotation_line);

            }

        },

        line_select: function(event,$line,id){
            var self = this;
            var order = this.pos.get_order();
            for (var quot_id in this.pos.quotations){
                if (this.pos.quotations[quot_id]['id'] == id){
                    var selected_quotation = this.pos.quotations[quot_id]
                }
            }
            if (selected_quotation){
                for (var line in this.pos.quotation_lines){
                    if (selected_quotation['lines'].indexOf(this.pos.quotation_lines[line]['id']) > -1 ){
                    var product_id = this.pos.db.get_product_by_id(this.pos.quotation_lines[line]['product_id'][0]);
                    this.pos.get_order().add_product(product_id,{ quantity: this.pos.quotation_lines[line]['qty']});
                    }
                }
                order.quotation_ref = selected_quotation;

                if (selected_quotation.partner_id){
                    var partner = this.pos.db.get_partner_by_id(selected_quotation.partner_id[0]);
                    order.set_client(partner);
                }
                this.gui.show_screen('products');
            }

        },

    });

    gui.define_screen({name:'PickupOrdersWidget', widget: PickupOrdersWidget});
});
