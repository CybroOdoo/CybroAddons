/** @odoo-module **/

    const PosComponent = require('point_of_sale.PosComponent');
    const { useListener } = require("@web/core/utils/hooks");
    const Registries = require('point_of_sale.Registries');
    class FindProductButton extends PosComponent {
        setup() {
        super.setup();
            useListener('click', this.onClick);
        }
       //To see the Find Product Screen
       async onClick() {
                this.showScreen('FindProductScreen');
       }
    }
    FindProductButton.template = 'FindProductButton';
    Registries.Component.add(FindProductButton);
    return FindProductButton;
