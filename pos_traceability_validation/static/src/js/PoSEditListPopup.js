odoo.define('pos_traceability_validation.PoSEditListPopup', function (require) {
    'use strict';
    const EditListPopup = require('point_of_sale.EditListPopup');
    const Registries = require('point_of_sale.Registries');
    const { _lt } = require('@web/core/l10n/translation');
    var rpc = require('web.rpc');
    /**
     * Extends EditListPopup for adding functionality for lot/ serial number
     * validation
     */
    const PoSEditListPopup = (EditListPopup) =>
        class extends EditListPopup {
            constructor() {
                super(...arguments);
                this.product = this.props.product;
            }
            /**
             * On confirming from the popup after adding lots/ serial numbers,
             * the values are passed to the function validate_lots() for the
             * validation. The corresponding error messages will be displayed
             * on the popup if the lot is invalid or duplicated, or there is
             * no insufficient stock.
             */
            async confirm() {
                if (this.props.title == 'Lot/Serial Number(s) Required') {
                    var lot_string = this.state.array;
                    var lot_names = [];
                    for (var i = 0; i < lot_string.length; i++) {
                        if (lot_string[i].text != '') {
                            lot_names.push(lot_string[i].text);
                        }
                    }
                    const picking_type_id = this.env.pos.config && this.env.pos.config.picking_type_id && this.env.pos.config.picking_type_id[0]
                    const result =  await rpc.query({
                        model: 'stock.production.lot',
                        method: 'validate_lots',
                        args: [lot_names, this.props.product, picking_type_id]
                    })
                    if (result != true) {
                        if(result[0] == 'no_stock') {
                            this.showPopup('ErrorPopup', {
                                'title': _lt('Out of stock'),
                                'body': _lt('The product is out of stock for ' + result[1] + '.')
                            });
                        } else if(result[0] == 'duplicate') {
                            this.showPopup('ErrorPopup', {
                                'title': _lt('Duplicate Serial Number'),
                                'body': _lt('Duplicate entry for ' + result[1] + '.')
                            });
                        } else if(result[0] == 'invalid') {
                            this.showPopup('ErrorPopup', {
                                'title': _lt('Invalid Lot/ Serial Number'),
                                'body': _lt('The Lot/ Serial Number ' + result[1] + ' is not available for this product.')
                            });
                        }
                    } else {
                        this.props.resolve({
                            confirmed: true,
                            payload: await this.getPayload()
                        });
                        this.trigger('close-popup');
                    }
                } else {
                    this.props.resolve({
                        confirmed: true,
                        payload: await this.getPayload()
                    });
                    this.trigger('close-popup');
                }
            }
        };
    Registries.Component.extend(EditListPopup, PoSEditListPopup);
    return EditListPopup;
});
