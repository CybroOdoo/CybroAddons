odoo.define('pos_refund_password.RefundPasswordButton', function (require) {
    'use strict';
    const PosComponent = require('point_of_sale.PosComponent');
    const ProductScreen = require('point_of_sale.ProductScreen');
    const Registries = require('point_of_sale.Registries');
    const { useListener } = require("@web/core/utils/hooks");
    const TicketScreen = require('point_of_sale.TicketScreen');
    const rpc = require("web.rpc");

     const PosResTicketScreen1 = (TicketScreen) =>
        class extends TicketScreen {
            async _onDoRefund() {
            var refund="";
            var session_refund= false;
            var data = await rpc.query({
                model: 'ir.config_parameter',
                method: 'get_param',
                args:["pos_refund_password.global_refund_security"],
            })
            .then(result =>{
                refund = result;
            });

            const dialogProps = {
            body : this.env._t(
                    'Incorrect Password')
                    };
            if (!refund){
                session_refund = this.env.pos.config.refund_security;
                }
            if(refund){
                const { confirmed, payload } = await this.showPopup('NumberPopup', { isPassword: true })
                if(refund == payload){
                    super._onDoRefund();
                }
                else{
                        this.showPopup('ErrorPopup',{
                        body : this.env._t('Invalid Password, Enter your global password'),
                        });
                    }
            }
            else if(session_refund){
                const { confirmed, payload } = await this.showPopup('NumberPopup', { isPassword: true })
                if(session_refund == payload){
                    super._onDoRefund();
                }
                else{
                        this.showPopup('ErrorPopup',{
                        body : this.env._t('Incorrect Password'),
                        });
                    }
            }
            else{
                super._onDoRefund();
            }
            }
        };
        Registries.Component.extend(TicketScreen, PosResTicketScreen1);
    });
