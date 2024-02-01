/**
 * @module pos_idle_time_session_lock.session_timer
 * @description This module handles the session timer for the Point of Sale idle time session lock feature.
 */
odoo.define('pos_idle_time_session_lock.session_timer', function (require) {
"use strict";
const Chrome = require('point_of_sale.Chrome');
var core = require('web.core');
const Registries = require('point_of_sale.Registries');
var _t = core._t;
var count_down_time;
/**
     * Customized Chrome component with session timer functionality.
     *
     * @class PosTimerChrome
     * @extends Chrome
     */
const PosTimerChrome = (Chrome) =>
        class extends Chrome {
            // Timer main function for set the timer
            set_timer() {
                var self = this;
                var count_down_time = this.env.pos.config.idle_time_limit
                var pos_lock = this.env.pos.config.pos_lock
                if (pos_lock){
                    var now = new Date().getTime();
                    var date = new Date(now);
                    date.setMinutes(date.getMinutes() + count_down_time);
                    var updatedTime = date.getTime();
                    var x = setInterval(function() {
                        var now = new Date().getTime();
                        var distance = updatedTime - now;
                        var days = Math.floor(distance / (1000 * 60 * 60 * 24));
                        var hours = Math.floor((distance % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
                        var minutes = Math.floor((distance % (1000 * 60 * 60)) / (1000 * 60));
                        var seconds = Math.floor((distance % (1000 * 60)) / 1000);
                        if (hours) {
                            this.body.children[1].querySelector('#times').textContent = hours + " h " + minutes + " m " + seconds + " s ";
                        } else {
                            this.body.children[1].querySelector('#times').textContent= minutes + " m " + seconds + " s ";
                        }
                        if (distance < 0) {
                            clearInterval(x);
                            if (self.env.pos.config.module_pos_hr) {
                                self.showTempScreen('LoginScreen');
                            }
                            else{
                                self.showTempScreen('LogoutScreen');
                            }
                        }
                    }, 1000);
                    /**
                        checking the mouse move event is occur
                    */
                    $(this.el.parentElement).mousemove(function (e) {
                        var now = new Date().getTime();
                        var date = new Date(now);
                        date.setMinutes(date.getMinutes() + count_down_time);
                        updatedTime = date.getTime();
                    });
                    /**
                        checking the key press event is occur
                    */
                    $(this.el.parentElement).keypress(function (e) {
                        var now = new Date().getTime();
                        var date = new Date(now);
                        date.setMinutes(date.getMinutes() + count_down_time);
                        updatedTime = date.getTime();
                    });
                    /**
                        checking the click event is occur
                    */
                    $(this.el.parentElement).click(function() {
                        var now = new Date().getTime();
                        var date = new Date(now);
                        date.setMinutes(date.getMinutes() + count_down_time);
                        updatedTime = date.getTime();
                    });
                }
            }
            /**
                Start the timer
            */
            async start() {
                await super.start();
                this.set_timer();
            }
            /**
                Open cash control function inherited for set the timer on it.
            */
            openCashControl() {
                this.set_timer()
                if (this.shouldShowCashControl()) {
                    this.showPopup('CashOpeningPopup');
                }
            }
        };
    Registries.Component.extend(Chrome, PosTimerChrome);
    return Chrome;
});
