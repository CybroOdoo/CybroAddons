odoo.define('pos_customer_wallet_management.customerListScreen', function (require) {
"use strict";

    var {PosGlobalState} = require('point_of_sale.models');
    const Registries = require('point_of_sale.Registries');
    const NewPosGlobalState = (PosGlobalState) => class NewPosGlobalState extends PosGlobalState {
         /**
         *Override PosGlobalState to load fields in pos session
         */
        async _processData(loadedData){
            await super._processData(...arguments);
            this.account_journal = loadedData['account.journal'];
            this.res_partner = loadedData['res.partner'];
            this.pos_payment_method = loadedData['pos.payment.method'];
        }
    }
Registries.Model.extend(PosGlobalState,NewPosGlobalState)

 const PartnerLine = require('point_of_sale.PartnerLine');
 const ExtendPartnerLine = (PartnerLine) =>
        class extends PartnerLine {
         /**
         *Override PartnerLine
         */
           wallet()
           {
           //Show wallet recharge screen
           var partner = this.props.partner;
           var data = this.env.pos.account_journal;
                this.showScreen('RechargeScreen', {
                      result : data,
                      partner : partner,
                });
           }
        }
    Registries.Component.extend(PartnerLine, ExtendPartnerLine);
    return PartnerLine;
});
