odoo.define('auto_logout_idle_user_odoo.systray', function(require) {
    "use strict";
    var SystrayMenu = require('web.SystrayMenu');
    var Widget = require('web.Widget');
    var ajax = require('web.ajax');
    var TimerWidget = Widget.extend({
        template: 'TimerSystray',
        willStart: function() {
            var self = this;
            return this._super().then(function() {
                self.get_idle_time();
            });
        },
        /**
        Getting minutes through python for the corresponding user
        */
        get_idle_time: function() {
            var self = this
            var now = new Date().getTime();
            ajax.rpc('/get_idle_time/timer').then(function(data) {
                if (data) {
                    self.minutes = data
                    self.idle_timer()
                }
            })
        },
        /**
        Passing values of the countdown to the xml
        */
        idle_timer: function() {
            var self = this;
            var nowt = new Date().getTime();
            var date = new Date(nowt);
            date.setMinutes(date.getMinutes() + self.minutes);
            var updatedTimestamp = date.getTime();
            /** Running the count down using setInterval function */
            var idle = setInterval(function() {
                var now = new Date().getTime();
                var distance = updatedTimestamp - now;
                var days = Math.floor(distance / (1000 * 60 * 60 * 24));
                var hours = Math.floor((distance % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
                var minutes = Math.floor((distance % (1000 * 60 * 60)) / (1000 * 60));
                var seconds = Math.floor((distance % (1000 * 60)) / 1000);
                if (hours && days) {
                    self.el.querySelector("#idle_timer").innerHTML = days + "d " + hours + "h " + minutes + "m " + seconds + "s ";
                } else if (hours) {
                    self.el.querySelector("#idle_timer").innerHTML = hours + "h " + minutes + "m " + seconds + "s ";
                } else {
                    self.el.querySelector("#idle_timer").innerHTML = minutes + "m " + seconds + "s ";
                    if(minutes == 1 && seconds == 0){
                         self.displayNotification({
                            message: ("You will be logged out in 1 minute."),
                            sticky: true,
                        })
                    }
                }
                /** If the countdown is zero the link is redirect to the login page*/
                if (distance < 0) {
                    clearInterval(idle);
                    self.el.querySelector("#idle_timer").innerHTML = "EXPIRED";
                    location.replace("/web/session/logout")
                }
            }, 1000);
            /**
            Checking if the onmousemove event is occur
            */
            document.onmousemove = () => {
                var nowt = new Date().getTime();
                var date = new Date(nowt);
                date.setMinutes(date.getMinutes() + self.minutes);
                updatedTimestamp = date.getTime();

            };
            /**
            Checking if the onkeypress event is occur
            */
            document.onkeypress = () => {
                var nowt = new Date().getTime();
                var date = new Date(nowt);
                date.setMinutes(date.getMinutes() + self.minutes);
                updatedTimestamp = date.getTime();
            };
            /**
            Checking if the onclick event is occur
            */
            document.onclick = () => {
                var nowt = new Date().getTime();
                var date = new Date(nowt);
                date.setMinutes(date.getMinutes() + self.minutes);
                updatedTimestamp = date.getTime();
            };
            /**
            Checking if the ontouchstart event is occur
            */
            document.ontouchstart = () => {
                var nowt = new Date().getTime();
                var date = new Date(nowt);
                date.setMinutes(date.getMinutes() + self.minutes);
                updatedTimestamp = date.getTime();
            }
            /**
            Checking if the onmousedown event is occur
            */
            document.onmousedown = () => {
                var nowt = new Date().getTime();
                var date = new Date(nowt);
                date.setMinutes(date.getMinutes() + self.minutes);
                updatedTimestamp = date.getTime();
            }
            /**
            Checking if the onload event is occur
            */
            document.onload = () => {
                var nowt = new Date().getTime();
                var date = new Date(nowt);
                date.setMinutes(date.getMinutes() + self.minutes);
                updatedTimestamp = date.getTime();
            }
        },
    });
    SystrayMenu.Items.push(TimerWidget);
})