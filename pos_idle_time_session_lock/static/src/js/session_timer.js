/**
 * @module pos_idle_time_session_lock.session_timer
 * @description This module handles the session timer for the Point of Sale idle time session lock feature.
 */
odoo.define('pos_idle_time_session_lock.session_timer', function (require) {
"use strict";
const Chrome = require('point_of_sale.Chrome');
const Registries = require('point_of_sale.Registries');
var time_limit;
var models = require('point_of_sale.models');
models.load_fields('pos.config',['idle_time_limit']);
const PosTimerChrome = (Chrome) =>
        class extends Chrome {
            /**
                Set a function to run a timer
            */
            set_timer(ev) {
                var self = this;
                var time_limit = this.env.pos.config.idle_time_limit
                this.env.pos_lock = this.env.pos.config.pos_lock
                var lock = this.env.pos_lock
                if (lock){
                    var now = new Date().getTime();
                    var date = new Date(now);
                    date.setMinutes(date.getMinutes() + time_limit);
                    var updatedTime = date.getTime();
                    var x = setInterval(function(ev) {
                        var now = new Date().getTime();
                        var distance = updatedTime - now;
                        var days = Math.floor(distance / (1000 * 60 * 60 * 24));
                        var hours = Math.floor((distance % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
                        var minutes = Math.floor((distance % (1000 * 60 * 60)) / (1000 * 60));
                        var seconds = Math.floor((distance % (1000 * 60)) / 1000);
                        if (hours) {
                            if (hours !== -1){
                                this.body.children[1].querySelector('#times').textContent = hours + " h " + minutes + " m " + seconds + " s ";
                            }
                        } else {
                            if (minutes !== -1){
                                this.body.children[1].querySelector('#times').textContent = minutes + " m " + seconds + " s ";
                            }
                        }
                        if (distance < 0) {
                            clearInterval(x);
                            self.showTempScreen('LoginScreen');
                        }
                    }, 1000);
                    /**
                        checking the mouse move event is occur
                    */
                    $(this.el.parentElement).mousemove(function (e) {
                        var now = new Date().getTime();
                        var date = new Date(now);
                        date.setMinutes(date.getMinutes() + time_limit);
                        updatedTime = date.getTime();
                    });
                    /**
                        checking the key press event is occur
                    */
                    $(this.el.parentElement).keypress(function (e) {
                        var now = new Date().getTime();
                        var date = new Date(now);
                        date.setMinutes(date.getMinutes() + time_limit);
                        updatedTime = date.getTime();
                    });
                    /**
                        checking the click event is occur
                    */
                    $(this.el.parentElement).click(function() {
                        var now = new Date().getTime();
                        var date = new Date(now);
                        date.setMinutes(date.getMinutes() + time_limit);
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
                this.set_timer();
                if (this.shouldShowCashControl()) {
                    this.showPopup('CashOpeningPopup', { notEscapable: true });
                }
            }
        };
    Registries.Component.extend(Chrome, PosTimerChrome);
    return Chrome;
});
