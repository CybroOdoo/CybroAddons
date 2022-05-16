odoo.define('advanced_pos_reports.ProductSummaryPopup', function(require) {
    'use strict';

    const { useState } = owl.hooks;
    const AbstractAwaitablePopup = require('point_of_sale.AbstractAwaitablePopup');
    const Registries = require('point_of_sale.Registries');
    const { _lt } = require('@web/core/l10n/translation');

    class ProductSummaryPopup extends AbstractAwaitablePopup {
        constructor() {
            super(...arguments);
            this.state = useState({
                current_session: false,
                start_date: "",
                end_date: ""
            });
        }
        click_is_session(){
            var is_session = $('#is_current_session').is(':checked');
            if(is_session){
                $("#date_section").hide();
            }
            else{
                $("#date_section").show();
            }
        }
        async confirm(event) {
            var is_session = this.state.current_session;
            var start_date = this.state.start_date || '';
            var end_date = this.state.end_date || '';
            var order = this.env.pos.get_order()['sequence_number']
            var domain = []
            if(is_session){
                domain = [['session_id', '=', this.env.pos.pos_session.id]]
            }
            else{
                domain = [['date_order', '>=', start_date + ' 00:00:00'],
                          ['date_order', '<=', end_date +  ' 23:59:59']]
            }
            var orders = await this.rpc({
				model: 'pos.order',
				method: 'search',
				args: [domain],
				});
            var order_ids = []
            $.each(orders,function(index,value){
                order_ids.push(value)
            });
            var products = await this.rpc({
				model: 'pos.order',
				method: 'get_product_summary',
				args: [order, order_ids],
				});
            this.showScreen('ProductSummaryReceiptScreen', { products: products, start_date: start_date, end_date: end_date});
            super.confirm();
        }
    }
    ProductSummaryPopup.template = 'ProductSummaryPopup';
    ProductSummaryPopup.defaultProps = {
        confirmText: _lt('Print'),
        cancelText: _lt('Cancel'),
        array: [],
        isSingleItem: false,
    };

    Registries.Component.add(ProductSummaryPopup);

    return ProductSummaryPopup;
});
