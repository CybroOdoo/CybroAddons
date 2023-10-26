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
models.load_fields('pos.config',['idle_time_limit','is_pos_lock']);
    const { useListener } = require('web.custom_hooks');
    const { onPatched, useExternalListener } = owl.hooks;
/**
     * Customized Chrome component with session timer functionality.
     *
     * @class PosTimerChrome
     * @extends Chrome
     */
const PosTimerChrome = (Chrome) =>
        class extends Chrome {
            setup(){
                super.setup();
                 useExternalListener(document, 'mousemove', this.move);
                 useExternalListener(document, 'click', this.move);
                 useExternalListener(document, 'keyup', this.move);
                this.interval ;
               onPatched(() =>{
               })
            }
            move(ev){
                      clearInterval(this.interval)
                      this.set_timer()
                    }
            convertMinuteSecondFormat(number){
                let minutes = Math.floor(number);
                let decimalPart = number % 1;
                let seconds = Math.round(decimalPart * 60);
                return {minutes, seconds}
            }
            set_timer() {
                var time_limit = this.env.pos.config.idle_time_limit
                document.getElementById("times").innerHTML = ''
                var self = this;
                this.env.is_pos_lock = this.env.pos.config.is_pos_lock
                var lock = this.env.is_pos_lock
                if (lock){
                    var now = new Date().getTime();
                    var date = new Date(now);
                    const { minutes, seconds } = this.convertMinuteSecondFormat(time_limit)
                    date.setMinutes(date.getMinutes() + minutes);
                    date.setSeconds(date.getSeconds() + seconds);
                    const additionalSeconds = 15000
                    var updatedTime = date.getTime() + additionalSeconds;
                    let securityIdleTime = additionalSeconds/1000
                    this.interval = setInterval(() => {
                        var now = new Date().getTime();
                        var distance = updatedTime - now;
                        var days = Math.floor(distance / (1000 * 60 * 60 * 24));
                        var hours = Math.floor((distance % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
                        var minutes = Math.floor((distance % (1000 * 60 * 60)) / (1000 * 60));
                        var seconds = Math.floor((distance % (1000 * 60)) / 1000);
                        securityIdleTime > 0 ? securityIdleTime -- : ''
                        if (securityIdleTime <= 0){
                            if (hours) {
                                document.getElementById("times").innerHTML = hours + " h " + minutes + " m " + seconds + " s ";
                            } else {
                                document.getElementById("times").innerHTML = minutes + " m " + seconds + " s ";
                            }
                        }
                        if (distance < 0) {
                            clearInterval(this.interval);
                            self.showTempScreen('LoginScreen');
                        }
                    }, 1000);
                }
            }
            async start() {
                await super.start();
                this.set_timer();
            }
            __closeTempScreen() {
                this.tempScreen.isShown = false;
                this.set_timer();
            }
        };
    Registries.Component.extend(Chrome, PosTimerChrome);
    return Chrome;
});
