odoo.define('laundry_management_pos.Custom', function (require) {
    'use strict';
    const { Gui } = require('point_of_sale.Gui');
    const PosComponent = require('point_of_sale.PosComponent');
    const Registries = require('point_of_sale.Registries');
    const { useListener } = require("@web/core/utils/hooks");
    const models = require('point_of_sale.models');

    // Extending the PosComponent that used to create a button in the POS View
    class CustomDemoButtons extends PosComponent {
        async setup() {
            super.setup();
            await this.loadDataFromWashingTypeModel();
        }
        async _onClickLaundry(e) {
        //Method corresponds to Laundry service button click
            const core = require('web.core');
            const _t = core._t;
            Gui.showPopup("LaundryServiceTypePopup", {
                title: _t("Laundry Service"),
                confirmText: _t("Exit"),
                service: this.env.pos.washing_type,
                pos: this.env.pos,
            });
        }
        async loadDataFromWashingTypeModel() {
        // Method for loading washing types
            const washingTypeData = await this.rpc({
                model: 'washing.type',
                method: 'search_read',
                fields: ['name', 'assigned_person', 'amount'],
            });
            this.env.pos.washing_type = washingTypeData;
        }
    }
    CustomDemoButtons.template = 'CustomDemoButtons';
    const ProductScreen = Registries.Component.get('ProductScreen');
    ProductScreen.addControlButton({
        component: CustomDemoButtons,
        condition: function () {
            return this.env.pos.config.orderline_washing_type;
        },
    });
    Registries.Component.add(CustomDemoButtons);
    return CustomDemoButtons;
});
