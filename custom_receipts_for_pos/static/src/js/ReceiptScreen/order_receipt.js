odoo.define('custom_receipts_for_pos.receipt',function(require){
    "use strict"
    const Registries = require('point_of_sale.Registries');
    const OrderReceipt = require('point_of_sale.OrderReceipt');

//    extending the pos receipt screen
    const PosResOrderReceipt = OrderReceipt =>
        class extends OrderReceipt {
             get receiptEnv() {
                let receipt_render_env = super.receiptEnv;
                let receipt = receipt_render_env.receipt;
                var self=this;
//                if there is a selected receipt in pos config replace that
//                receipt with existing one
                if(self.env.pos.config.is_custom_receipt){
                    var receipt_design=self.env.pos.config.design_receipt
                    var order=self._receiptEnv.order;
                    var data={
                        widget:self.env,
                        pos:order.pos,
                        order:order,
                        receipt:order.export_for_printing(),
                        orderlines:order.get_orderlines(),
                        paymentlines:order.get_paymentlines(),
                        moment:moment,
                        };
                    var parser=new DOMParser();
                    var xmlDoc=parser.parseFromString(receipt_design,
                    "text/xml");
                    var s=new XMLSerializer();
                    var newXmlStr=s.serializeToString(xmlDoc);
                    var qweb=new QWeb2.Engine();
                    qweb.add_template('<templates><t t-name="receipt_design">'
                    +newXmlStr+'</t></templates>');
                    receipt=qweb.render('receipt_design',data);$(
                    'div.pos-receipt').replaceWith(receipt);
                    return receipt_render_env;
                    }
                return receipt_render_env;
                }
            }
    Registries.Component.extend(OrderReceipt, PosResOrderReceipt)
    return OrderReceipt
});