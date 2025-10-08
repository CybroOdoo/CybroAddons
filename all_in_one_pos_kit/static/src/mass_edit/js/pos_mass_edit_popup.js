odoo.define('all_in_one_pos_kit.pos_mass_edit_popup', function(require) {
    'use strict';
    const AbstractAwaitablePopup = require('point_of_sale.AbstractAwaitablePopup');
    const Registries = require('point_of_sale.Registries');
    class MassEditPopup extends AbstractAwaitablePopup {
        async confirm(){
        //    Function for confirm button inside popup
            window.location.reload();
        }
        sendInput(key) {
        //        Function to change quantity into 0
            _.each(this.props.body, function(edit) {
                if (edit.id == key){
                    edit.quantity = 0
                }
            });
        }
    }
    MassEditPopup.template = 'MassEditPopup';
    MassEditPopup.defaultProps = {
    confirm: "Confirm",
    cancel: "Cancel",
    };
  Registries.Component.add(MassEditPopup);
  return MassEditPopup;
});
