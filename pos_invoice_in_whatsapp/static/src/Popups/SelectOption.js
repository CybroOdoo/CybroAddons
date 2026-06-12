/** @odoo-module **/
/**The 'WtspMessagePopup' class extends 'AbstractAwaitablePopup' and is designed to interact with the Point of Sale.
Retrieve order details and populate the popup content with the order's product information.
Handle the confirmation action, send a custom message associated with the order.*/
    var rpc = require('web.rpc');
    import { useBus, useService } from "@web/core/utils/hooks";
    const AbstractAwaitablePopup = require('point_of_sale.AbstractAwaitablePopup');
    const { Gui } = require('point_of_sale.Gui');
    const { _t } = require('web.core');
    const Registries = require('point_of_sale.Registries');
    var emailTemplate;
    var end_tag;
    var product_html ;
    var price_html;
    var quantity_html;
    var html_end;
    var text_msg;
    var option_name;
    class WtspMessagePopup extends AbstractAwaitablePopup {
//        Getting text invoice data.
        async getValue(ev)
        {
          const orderData = this.env.pos.get_order();
        var appendDiv = document.createElement("div");
        orderData.orderlines.forEach((line) => {
            var htmlDiv = document.createElement('div');
            product_html = document.createElement('span');
            product_html.innerText = line.product.display_name
            htmlDiv.appendChild(product_html);
            price_html = document.createElement('span');
            price_html.innerText = line.price
            htmlDiv.appendChild(price_html);
            quantity_html = document.createElement('span');
            appendDiv.appendChild(htmlDiv);
        })
        emailTemplate = '<div style="font-family: Ubuntu, Arial, Verdana, sans-serif; font-size:+ 12px;margin-bottom: 1rem;"><p style="margin: 0; padding: 0; font-size: 13px; ">Order Name:'+orderData.name+'</p><p style="margin: 0; padding: 0; font-size: 13px; ">Hello '+orderData.partner.name+' Greetings from '+orderData.pos.company.name+''+ orderData.pos.company.currency_id[1]+  ' Following is your order details </p></div>';
        document.querySelector('.order_line_content').innerHTML= emailTemplate;
        document.querySelector('.order_line_content').appendChild(appendDiv)
        }
//        When confirming the message type pos_reference,option_name pass to the account.move function.
        async confirm(e){
                var option=document.getElementsByName("option");
                var pos_reference=this.env.pos.get_order().name
                    for (var i = 0; i < option.length; i++) {
                        if (option[i].checked){
                            option_name=option[i].getAttribute('string');
                            rpc.query({
                            model: 'account.move',
                            method: 'action_send_message',
                            args: [,pos_reference,option_name]
                                }).then(function(result) {
                                    if(result!=200){
                                    Gui.showPopup("ErrorPopup", {
                                            'title': _t("Validation Error"),
                                            'body':  _t("Check your Authentication Token."),
                                        });
                                    }
                            })
                        }
                    }
                                    this.cancel();
        }
        }
    WtspMessagePopup.template = 'WtspMessagePopup';
    WtspMessagePopup.defaultProps= { confirmKey: false };
    Registries.Component.add(WtspMessagePopup);
