odoo.define('pos_book_order.buttons', function (require) {
"use strict";
    var screens = require('point_of_sale.screens');
    var core = require('web.core');
    var gui = require('point_of_sale.gui');
    var _t = core._t;

    var button_book_order = screens.ActionButtonWidget.extend({
        template: 'button_book_order',
        button_click: function () {
        var order = this.pos.get_order();
        var widget = this.pos.get_client()
        var order_lines = this.pos.get_order().get_orderlines();
        this.gui.show_popup('popup_widget',{
                title: _t('Book Order'),
            });
        },
    });

    screens.define_action_button({
        'name': 'book_order',
        'widget': button_book_order
    });

    screens.OrderWidget.include({
        update_summary: function(){
            this._super();
            var changes = this.pos.get_order();
            var buttons = this.getParent().action_buttons;
            if(changes.orderlines.length != 0 ){
                    if (buttons && buttons.book_order) {
                            buttons.book_order.highlight(changes);
                        }
                }
            else if (buttons && buttons.book_order) {
                            buttons.book_order.highlight();
                        }
        },
    });

});


