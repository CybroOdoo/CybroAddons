/* @odoo-module */

import { Component, useState, onWillStart } from "@odoo/owl";
import { rpc } from "@web/core/network/rpc";
import { registry } from "@web/core/registry";
import { session } from "@web/session";

import { _t } from "@web/core/l10n/translation";

class TimerSystrayItem extends Component{
    static template= "auto_logout_idle_user_odoo.TimerSystray"
    setup(){
        this.state = useState({
           idle_time: null,
        })

        onWillStart(async () => {
            var self = this
            var now = new Date().getTime();
            rpc('/get_idle_time/timer', {
            }).then((data) => {
                if (data) {
                    self.minutes = data
                    self.idle_timer()
                }
             });
        });

    }
    /**
    passing values of the countdown to the xml
    */
    idle_timer() {
        var self = this
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
                self.state.idle_time = days + "d " + hours + "h " + minutes + "m " + seconds + "s ";
            } else if (hours) {
                self.state.idle_time = hours + "h " + minutes + "m " + seconds + "s ";
            } else {
                self.state.idle_time = minutes + "m " + seconds + "s ";
            }
            /** if the countdown is zero the link is redirect to the login page*/
            if (distance < 0) {
                clearInterval(idle);
                self.state.idle_time = "EXPIRED";
                location.replace("/web/session/logout")
            }
        }, 1000);
        /**
        checking if the onmouse-move event is occur
        */
        document.onmousemove = () => {
            var nowt = new Date().getTime();
            var date = new Date(nowt);
            date.setMinutes(date.getMinutes() + self.minutes);
            updatedTimestamp = date.getTime();
        };
         /**
        checking if the onkeypress event is occur
        */
        document.onkeypress = () => {
            var nowt = new Date().getTime();
            var date = new Date(nowt);
            date.setMinutes(date.getMinutes() + self.minutes);
            updatedTimestamp = date.getTime();
        };
        /**
        checking if the onclick event is occur
        */
        document.onclick = () => {
            var nowt = new Date().getTime();
            var date = new Date(nowt);
            date.setMinutes(date.getMinutes() + self.minutes);
            updatedTimestamp = date.getTime();
        };
        /**
        checking if the ontouchstart event is occur
        */
        document.ontouchstart = () => {
            var nowt = new Date().getTime();
            var date = new Date(nowt);
            date.setMinutes(date.getMinutes() + self.minutes);
            updatedTimestamp = date.getTime();
        }
        /**
        checking if the onmousedown event is occur
        */
        document.onmousedown = () => {
            var nowt = new Date().getTime();
            var date = new Date(nowt);
            date.setMinutes(date.getMinutes() + self.minutes);
            updatedTimestamp = date.getTime();
        }
        /**
        checking if the onload event is occur
        */
        document.onload = () => {
            var nowt = new Date().getTime();
            var date = new Date(nowt);
            date.setMinutes(date.getMinutes() + self.minutes);
            updatedTimestamp = date.getTime();
        }
    }
}
export const systrayItem = {
    Component: TimerSystrayItem
};
registry.category("systray").add("auto_logout_idle_user_odoo.TimerSystray",systrayItem, {sequence:25});
