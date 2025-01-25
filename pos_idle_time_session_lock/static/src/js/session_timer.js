/** @odoo-module **/
import { Chrome } from "@point_of_sale/app/pos_app";
import { Navbar } from "@point_of_sale/app/navbar/navbar";
import { patch } from "@web/core/utils/patch";
import { onWillUnmount, reactive, useEffect, useExternalListener, useRef, useState, onWillStart } from "@odoo/owl";
import { usePos } from "@point_of_sale/app/store/pos_hook";

var updatedTime;

patch(Navbar.prototype, {
    setup() {
        super.setup(...arguments);
        useExternalListener(window, "click", this.onWindowClick, true);
        useExternalListener(window, "keypress", this.onWindowKeypress, true);
        this.rootRef = useRef("root");
        this.timerState = useState({ time: null });
        this.count_down_time = this.pos.config.idle_time_limit || 0;
        onWillStart(() => this.set_timer());
    },
    set_timer() {
        var self = this;
        var count_down_time = self.count_down_time;
        var pos_lock = self.pos.config.pos_lock;
        if (pos_lock) {
            var now = new Date().getTime();
            var date = new Date(now);
            date.setMinutes(date.getMinutes() + count_down_time);
            updatedTime = date.getTime();
            var x = setInterval(function() {
                var now = new Date().getTime();
                var distance = updatedTime - now;
                var days = Math.floor(distance / (1000 * 60 * 60 * 24));
                var hours = Math.floor((distance % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
                var minutes = Math.floor((distance % (1000 * 60 * 60)) / (1000 * 60));
                var seconds = Math.floor((distance % (1000 * 60)) / 1000);
                self.timerState.time = hours + " h " + minutes + " m " + seconds + " s ";
                if (distance <= 0) {
                    clearInterval(x);
                    if (self.pos.config.module_pos_hr) {
                        self.pos.showScreen("LoginScreen");
                    } else {
                        self.pos.showScreen("LoginScreen");
                    }
                }
            }, 1000);
        }
    },
    onWindowClick() {
        this.set_timer();
        this.resetTimer();
    },
    onWindowKeypress() {
        this.resetTimer();
    },
    resetTimer() {
        var now = new Date().getTime();
        var date = new Date(now);
        date.setMinutes(date.getMinutes() + this.count_down_time);
        updatedTime = date.getTime();
    },
});