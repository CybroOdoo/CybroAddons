/** @odoo-module **/
odoo.define('pos_weight_manual.PosGlobalState', function (require) {
    'use strict';
    var { PosGlobalState } = require('point_of_sale.models');
    const Registries = require('point_of_sale.Registries');
    var models = require('point_of_sale.models');
    // Load 'res.config.settings' model fields
    models.load_models([{
        model: 'res.config.settings',
        fields: ['is_allow_manual_weight'],
        loaded: function (self, is_allow_manual_weight) {
            self.is_allow_manual_weight = is_allow_manual_weight;
        }
    }]);

    const NewPosGlobalStateManual = (PosGlobalState) => class NewPosGlobalStateManual extends PosGlobalState {
       async _processData(loadedData) {
       // load field that in res.config.settings into pos.
         await super._processData(...arguments);
         this.is_allow_manual_weight = loadedData['res.config.settings'];
         }
    }
Registries.Model.extend(PosGlobalState, NewPosGlobalStateManual);
return NewPosGlobalStateManual;
});