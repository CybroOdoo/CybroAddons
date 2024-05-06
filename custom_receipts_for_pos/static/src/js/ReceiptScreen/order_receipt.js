odoo.define('custom_receipts_for_pos.receipt',function(require){
    "use strict"
    const Registries = require('point_of_sale.Registries');
    const OrderReceipt = require('point_of_sale.OrderReceipt');

//    extending the pos receipt screen
    const PosResOrderReceipt = OrderReceipt =>
        class extends OrderReceipt {
            mounted() {
                let receipt_render_env = super.receiptEnv;
                let receipt = receipt_render_env.receipt;
                   if(this.env.pos.config.is_custom_receipt){
                        var receipt_design=this.env.pos.config.design_receipt;
                        var order=this._receiptEnv.order;
                        var data={
                            widget:this.env,
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
                        receipt=qweb.render('receipt_design',data);
                        $('div.pos-receipt').replaceWith(receipt);
                   }
            }
        }
    Registries.Component.extend(OrderReceipt, PosResOrderReceipt)
    return OrderReceipt
});
