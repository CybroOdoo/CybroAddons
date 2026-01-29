/** @odoo-module **/
odoo.define('pos_reference_for_payment.PosGlobalState', function (require) {
    'use strict';
    var rpc = require('web.rpc')
    var { PosGlobalState, Order } = require('point_of_sale.models');
    const Registries = require('point_of_sale.Registries');
    var models = require('point_of_sale.models');
        // Load models to retrieve configuration and account move data
        // Load 'pos.payment' model fields
    models.load_models([{
        model: 'pos.payment',
        fields: ['user_payment_reference'],
        loaded: function (self, user_payment_reference) {
            self.user_payment_reference = user_payment_reference;
        }
    }]);
       // Load 'res.config.settings' model fields
    models.load_models([{
        model: 'res.config.settings',
        fields: ['is_allow_payment_ref'],
        loaded: function (self, is_allow_payment_ref) {
            self.is_allow_payment_ref = is_allow_payment_ref;
        }
    }]);
//    Extend POS global state
//    const Registries = require('point_of_sale.Registries');
    const NewPosGlobalState = (PosGlobalState) => class NewPosGlobalState extends PosGlobalState {
       async _processData(loadedData) {
         await super._processData(...arguments);
         // Load field values of in pos.payment into pos.
         this.user_payment_reference = loadedData['pos.payment'];
         // Load field values of in res.config.settings into pos.
         this.is_allow_payment_ref = loadedData['res.config.settings'];
         }
    }
Registries.Model.extend(PosGlobalState, NewPosGlobalState);
 return NewPosGlobalState;
});
