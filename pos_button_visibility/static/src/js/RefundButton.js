odoo.define('pos_button_visibility.RefundButton', function (require) {
    'use strict';
    const Registries = require('point_of_sale.Registries');
    const RefundButton = require('point_of_sale.RefundButton');
    var rpc = require('web.rpc');
    var { PosGlobalState } = require('point_of_sale.models');
    /** Extends PosGlobalState to load model to pos **/
    const PosSessionGlobalState = (PosGlobalState) => class PosSessionGlobalState extends PosGlobalState {
        async _processData(loadedData) {
            await super._processData(loadedData);
            this.res_user = loadedData['res.users'];
            this.user_session = loadedData['user_session_ids'];
            this.buttons_pos = loadedData['buttons_pos_ids']
        }
    }
    Registries.Model.extend(PosGlobalState, PosSessionGlobalState);
    /** Extend RefundButton to add function **/
    const PosButton = (RefundButton) =>
        class  extends RefundButton {
            /** To set up the RefundButton **/
            setup() {
                super.setup(...arguments);
                this.env.pos.user_session = []
                this.env.pos.button =[]
                this.userItem()
            }
            /** This is used to get the sessions and  buttons**/
             async userItem(){
                var session;
                if (this.env.pos.res_user.length !== 0)
                {
                    var session = this.env.pos.res_user.user_session_ids;}
                else{
                    session = false
                }
                var buttons;
                if (this.env.pos.res_user.length !== 0)
                {
                    var buttons = this.env.pos.res_user.buttons_pos_ids;}
                else{
                    buttons = false
                }
                var def = await rpc.query({
                model: 'res.users',
                method: 'pos_button_visibility',
                args: [,buttons]
                })
                this.env.pos.user_session = session
                this.env.pos.button = def
             }
        };
    Registries.Component.extend(RefundButton, PosButton)
    return RefundButton
});
