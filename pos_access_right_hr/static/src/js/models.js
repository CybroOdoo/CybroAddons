odoo.define('pos_access_right_hr.Access_Right', function(require) {
 'use strict';
    var { PosGlobalState, Order} = require('point_of_sale.models');
    const Registries = require('point_of_sale.Registries');
    const PosSessionOrdersPosGlobalStateExtend = (PosGlobalState) => class PosSessionOrdersPosGlobalStateExtend extends PosGlobalState {
    //To load hr.employee fields to pos session
        async _processData(loadedData) {
            await super._processData(...arguments);
            this.session_access = loadedData['hr.employee'];
        }
    }
    Registries.Model.extend(PosGlobalState, PosSessionOrdersPosGlobalStateExtend);
});
