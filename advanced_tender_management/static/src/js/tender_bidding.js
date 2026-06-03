/** @odoo-module **/

import { jsonrpc } from "@web/core/network/rpc_service";
import publicWidget from '@web/legacy/js/public/public_widget';

publicWidget.registry.TenderBiddingForm=publicWidget.Widget.extend({
    selector:'.tender_details_page',
    events:{
        'change .vendor_bid':'_onChangeComputeTotal',
        'click .edit-request-btn':'_onClickEditRequest'
    },
    _onClickEditRequest: async function(ev){
        var value=$('.bid_info').attr('data-bid_id');
        await jsonrpc('/edit_request',{'bid_id':value}).then((result)=>{
            window.location.href = '/edit_request_success'
        })
        },
    _onChangeComputeTotal: async function(ev){
        $('.hidden_price_input').remove();
        var targetRow = ev.target.closest('tr');
        var vendor_price=ev.target.value
        var product_qty=targetRow.querySelector('.product_qty').textContent.replace(',','')
        var total_price=parseInt(product_qty)*parseFloat(vendor_price)
        targetRow.querySelector('.total_price').textContent=total_price.toFixed(2);
        var grandTotal = 0;
        var allProductRows=ev.target.closest('tbody').querySelectorAll('.product_row');
        var productList=Array.from(allProductRows).map(row=>{
        var inputElement = row.querySelector('.vendor_bid');
        var productId = inputElement.getAttribute('product_id');
        var value = inputElement.value;
        var qty = parseFloat(row.querySelector('.product_qty').textContent.replace(',', '')) || 0;
        var rowTotalPrice = qty * value;
        grandTotal += rowTotalPrice;
        return [productId,value]
        })
        var totalRow = ev.target.closest('tbody').querySelector('.total_row .grand_total');
        if (totalRow) {
            totalRow.textContent = grandTotal.toFixed(2);
        }
        $('.tender-bid-form').append(`<input type="hidden" class="hidden_price_input" name="product_bid_list" value='${JSON.stringify(productList)}'>`);
    }
})


