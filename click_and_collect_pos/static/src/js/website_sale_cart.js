/** @odoo-module */
import  {websiteSaleCart}  from "@website_sale/js/website_sale";
import publicWidget from "@web/legacy/js/public/public_widget";
import { rpc } from "@web/core/network/rpc";

//Adding the custom button
publicWidget.registry.websiteSaleCart .include({
   events: Object.assign({}, publicWidget.Widget.prototype.events, {
    'click .clickandecollect': '_onClickClickAndCollect',
    'click .session_values': '_onClickPosConfig',
    'click .js_delete_product': '_onClickDeleteProduct',
  }),
  _onClickClickAndCollect(ev){
    const order_id = $(ev.target).data('id');
    const pos_conf = $(ev.currentTarget.parentElement.parentElement).find('.oe_session');
    if ($(ev.target).is(':checked')) {
       pos_conf.removeClass('d-none');
    }else {
		pos_conf.addClass('d-none')
			}
    rpc('/web/dataset/call_kw', {
      model: 'sale.order.line',
      method: 'write',
      args: [
        [order_id],
        {'is_click_and_collect': ev.currentTarget.checked,},
        ],
       kwargs: {},
    });
  },
  _onClickDeleteProduct(ev) {
    ev.preventDefault();
    $(ev.currentTarget).closest('.o_cart_product').find('.js_quantity').val(0).trigger('change');
  },
  _onClickPosConfig(ev) {
    const closestCheck = $(ev.currentTarget.parentElement.parentElement).find('.clickandecollect');
    const order_id = closestCheck.data('id');
    const session_id = $(ev.target).val();
    var m= rpc('/web/dataset/call_kw', {
      model: 'sale.order.line',
      method: 'write',
      args: [
        [order_id],
        {
          'pos_config_id': parseInt(session_id),
        },
      ],
       kwargs: {},
    });
  },
});
