odoo.define('custom_receipts_for_pos.design_receipt',function(require){
    "use strict"
    const Registries = require('point_of_sale.Registries');
    var PosDB = require("point_of_sale.DB");
    const OrderReceipt = require('point_of_sale.OrderReceipt');
    const { onMounted } = owl.hooks;
    /*The function is used to add method init to an existing object PosDB.*/
    PosDB.include({
        init:function(options)
        {
            this._super(options);
            this.receipt_design_id=null;
        },
    })
    /* Extends OrderReceipt to add new designs for receipt, here call the
    template of customised record and add to the registry.*/
    const PosResOrderReceipt = OrderReceipt =>
        class extends OrderReceipt {
            constructor() {
                super(...arguments);
                onMounted(() =>{
                    if(this.env.pos.config.is_custom_receipt){
                        var receipt_design_id=this.env.pos.config.design_receipt
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
                        var xmlDoc=new DOMParser().parseFromString(receipt_design_id,"text/xml");
                        var newXmlStr=new XMLSerializer().serializeToString(xmlDoc);
                        var qweb=new QWeb2.Engine();
                        qweb.add_template('<templates><t t-name="receipt_design_id">'+newXmlStr+'</t></templates>');
                        var receipt=qweb.render('receipt_design_id',data);$('div.pos-receipt').replaceWith(receipt);
                        }
                    })
                }
            }
    Registries.Component.extend(OrderReceipt, PosResOrderReceipt)
});