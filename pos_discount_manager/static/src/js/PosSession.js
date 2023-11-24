odoo.define('pos_discount_manager.PosSession', function(require) {
    'use strict';

   var {PosGlobalState} = require('point_of_sale.models');
   const Registries = require('point_of_sale.Registries');
   const NewPosGlobalState = (PosGlobalState) => class NewPosGlobalState extends PosGlobalState {
         /**
         *Override PosGlobalState to load fields in pos session
         */
     async _processData(loadedData) {
        await super._processData(...arguments);
        this.hr_employee = loadedData['hr.employee'];
     }
   }
   Registries.Model.extend(PosGlobalState,NewPosGlobalState)
   });
