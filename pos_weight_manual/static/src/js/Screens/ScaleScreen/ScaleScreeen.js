/** @odoo-module **/

    const ScaleScreen = require('point_of_sale.ScaleScreen');
    const Registries = require('point_of_sale.Registries');

    const ManualWeightScaleScreen = ScaleScreen =>
        class extends ScaleScreen {
             addManualWeight(){
             // Add user entered weight into scale weight.
               var manual_weight = Number(document.getElementById("qty_to_add").value)
               this.env.proxy.debug_set_weight(manual_weight);
             }
        };

    Registries.Component.extend(ScaleScreen, ManualWeightScaleScreen);
    return ScaleScreen;
