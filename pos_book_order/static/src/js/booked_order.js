odoo.define('pos_book_order.BookedOrder',function(require){
"use strict";

    var gui = require('point_of_sale.gui');
    var chrome = require('point_of_sale.chrome');
    var core = require('web.core');
    var models = require('point_of_sale.models');
    var PosModelSuper = models.PosModel;
    var pos_screens = require('point_of_sale.screens');
    var QWeb = core.qweb;
    var _t = core._t;


    var BookedOrderButton = pos_screens.ActionButtonWidget.extend({
        template: 'BookedOrderButton',
        count: function() {
        if (this.pos.quotations) {
            return this.pos.quotations.length;
            } else {
                return 0;
            }
        },
        button_click: function(){
            if (this.pos.get_order().get_orderlines().length === 0){
                this.gui.show_screen('BookedOrdersWidget');

            }
            else{
                this.gui.show_popup('error',{
                    title :_t('Process Only one operation at a time'),
                    body  :_t('Process the current order first'),
                });
            }
        }
    });

    pos_screens.define_action_button({
        'name': 'Show Order',
        'widget': BookedOrderButton,
    });


    var BookedOrdersWidget = pos_screens.ScreenWidget.extend({
        template: 'BookedOrdersWidget',
        init: function(parent, options){
            this._super(parent, options);
        },
        show: function(){
            var self = this;
            this._super();
            this.renderElement();
            this.$('.back').click(function () {
                self.gui.show_screen('products');
            });
            this.$('.pickup').click(function(){
                self.gui.show_screen('PickupOrdersWidget');
            });
            this.$('.delivery').click(function(){
                self.gui.show_screen('DeliveryOrdersWidget');
            });

            var quotations = this.pos.quotations;
            this.render_list(quotations);

             this.$('.order-list-contents').delegate('.order-line .confirm_pos_order','click',function(event){
                self.line_select(event,$(this.parentElement.parentElement),parseInt($(this.parentElement.parentElement).data('id')))
            });

            var search_timeout = null;

            if(this.pos.config.iface_vkeyboard && this.chrome.widget.keyboard){
                this.chrome.widget.keyboard.connect(this.$('.searchbox input'));
            }

            this.$('.searchbox input').on('keyup',function(event){
                clearTimeout(search_timeout);
                var query = this.value;
                search_timeout = setTimeout(function(){
                    self.perform_search(query,event.which === 13);
                },70);
            });

            this.$('.searchbox .search-clear').click(function(){
                self.clear_search();
            });
        },

        render_list: function(quotations){
            var length = quotations.length
            var contents = this.$el[0].querySelector('.order-list-contents');
            contents.innerHTML = "";
            for(var i = 0, len = Math.min(quotations.length,1000); i < len; i++){
                var quotation    = quotations[i];
                var quotation_line_html = QWeb.render('BookedOrderLIne',{widget: this, quotation:quotations[i]});
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

                var orders = this.pos.get('selectedOrder')
                var selected_orderline = orders.selected_orderline
                selected_orderline.trigger('change', selected_orderline);


                this.gui.show_screen('products');
            }

        },

        perform_search: function(query, associate_result){
            var quotations;
            if(query){
                quotations = this.search_quotation(query);
                this.render_list(quotations);
            }else{
                quotations = this.pos.quotations;
                this.render_list(quotations);
            }
        },
        clear_search: function(){
            var quotations = this.pos.quotations;
            this.render_list(quotations);
            this.$('.searchbox input')[0].value = '';
            this.$('.searchbox input').focus();
        },

        search_quotation: function(query){
            try {
                var re = RegExp(query);
            }catch(e){
                return [];
            }
            var results = [];
            for (var quot_id in this.pos.quotations){
                var r = re.exec(this.pos.quotations[quot_id]['name']);
                if(r){
                results.push(this.pos.quotations[quot_id]);
                }
            }
            return results;

        },

    });

    gui.define_screen({name:'BookedOrdersWidget', widget: BookedOrdersWidget});

});
