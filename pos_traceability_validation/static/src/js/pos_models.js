odoo.define('pos_traceability_validation.pos_models', function (require) {
"use strict";
 /**
     * EditListPopup Override
     *
     * This module overrides the EditListPopup component in the Point of Sale (POS) module
     * to add custom behavior for serial number validation.
     */
    const EditListPopup = require('point_of_sale.EditListPopup');
    const Registries = require('point_of_sale.Registries');
    var rpc = require('web.rpc');
    const PosEditlistpopup = (EditListPopup) =>
        class extends EditListPopup {
        /**
             * Confirm Override
             *
             * Overrides the base confirm method to handle serial number validation.
             * If the title of the popup is 'Lot/Serial Number(s) Required', it validates
             * the entered lot numbers using the 'serial_no.validation' model.
             */
             async confirm() {
                 if (this.props.title == 'Lot/Serial Number(s) Required'){
                         var lot_string = this.state.array
                         var lot_names = [];
                         for (var i = 0; i < lot_string.length; i++) {
                            if (lot_string[i].text != ""){
                                lot_names.push(lot_string[i].text);
                            }
                         }
                         const result =  await rpc.query({
                                                model: 'serial_no.validation',
                                                method: 'validate_lots',
                                                args: [lot_names]
                                                })
                            if(result != true){
                                if(result[0] == 'no_stock'){
                                    this.showPopup('ErrorPopup', {
                                        'title': this.env._t('Insufficient stock'),
                                        'body': this.env._t("Insufficient stock for " + result[1]),
                                    });
                                }
                                else if(result[0] == 'duplicate'){
                                    this.showPopup('ErrorPopup', {
                                        'title': this.env._t('Duplicate entry'),
                                        'body': this.env._t("Duplicate entry for " + result[1]),
                                    });
                                }
                                else if(result[0] == 'except'){
                                    alert("Exception occurred with " + result[1])
                                    this.showPopup('ErrorPopup', {
                                        'title': this.env._t('Exception'),
                                        'body': this.env._t("Exception occurred with" + result[1]),
                                    });
                                }
                            }
                            else{
                                    this.props.resolve({ confirmed: true, payload: await this.getPayload() });
                                    this.trigger('close-popup');
                            }
                 }
                 else{
                        this.props.resolve({ confirmed: true, payload: await this.getPayload() });
                        this.trigger('close-popup');
                 }
            }
        };
    Registries.Component.extend(EditListPopup, PosEditlistpopup);
    return EditListPopup;
});
