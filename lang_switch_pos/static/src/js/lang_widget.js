odoo.define('product_multi_uom_pos.multi_uom_widget',function(require) {
    "use strict";
    const PosComponent = require('point_of_sale.PosComponent');
    const Registries = require('point_of_sale.Registries');
    var rpc = require('web.rpc');
    var { PosGlobalState, Order } = require('point_of_sale.models');
    const AbstractAwaitablePopup =
    require('point_of_sale.AbstractAwaitablePopup');
    const { onMounted } = owl;

//to show the activated languages in popup
    const PosHrPosGlobalState = (PosGlobalState) =>
    class PosHrPosGlobalState extends PosGlobalState {
        async _processData(loadedData) {
            await super._processData(...arguments);
                this.lang = loadedData['res.lang'];
        }}
        Registries.Model.extend(PosGlobalState, PosHrPosGlobalState);
    class LangWidget extends PosComponent {
        setup() {
            super.setup();
            this.lang_list = [];
            onMounted(this.onMounted);
            this.lang_list = this.env.pos.lang;
            }
//Pushing the languages at DOM mount
        onMounted(){
            this.lang_list = this.env.pos.lang;
            this.current_lang = this.env.pos.user.lang;
            console.log(this.current_lang);
            this.render();
        }
//Click events
    click_confirm(){
        var self = this;
        var lang = parseInt($('.lang').val());
            rpc.query({
                model: 'pos.order',
                method: 'switch_lang',
                args: [lang],
            })
        this.env.posbus.trigger('close-popup', {
                popupId: this.props.id,
                response: { confirmed: true, payload: null },
            });
    }
    click_cancel(){
        this.env.posbus.trigger('close-popup', {
                popupId: this.props.id,
                response: { confirmed: false, payload: null },
            });
    }
    }
    LangWidget.template = 'LangWidget';
    LangWidget.defaultProps = {
        confirmText: 'Return',
        cancelText: 'Cancel',
        title: 'Confirm ?',
        body: '',
    };
    Registries.Component.add(LangWidget);
    return LangWidget;
});

