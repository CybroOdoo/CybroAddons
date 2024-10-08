/** @odoo-module **/
import { Component } from "@odoo/owl";
import { session } from "@web/session";
import { ThemeStudioWidget } from "./ThemeStudioWidget";
import { onWillStart } from "@odoo/owl";

export class TimePicker extends ThemeStudioWidget {
    /**
     * @odoo-prop template
     * Defines the template for the TimePicker component.
     */
    static template = 'backend_theme_infinito.theme_advance';
    setup(){
       super.setup();
       onWillStart(this.onWillStart);
    }
    constructor() {
        super(...arguments);
        this.hhr = null;
        this.hmin = null;
        this.timer = null;
        this.minhr = 1;
        this.maxhr = 12;
        this.minmin = 0;
        this.maxmin = 59;
        this.setfield = null;
        this.set24 = false;
        this.setafter = null;
    }

    onWillStart() {
        super.onWillStart(...arguments);
        this.hhr = this.el.querySelector('#tp-hr');
        this.hmin = this.el.querySelector('#tp-min');
        for (let segment of ["hr", "min"]) {
            let up = this.el.querySelector(`#tp-${segment} .tp-up`);
            let down = this.el.querySelector(`#tp-${segment} .tp-down`);
            this["h"+segment] = this.el.querySelector(`#tp-${segment} .tp-val`);
            up.addEventListener('mousedown', () => { this.spin(true, segment); });
            down.addEventListener('mousedown', () => { this.spin(false, segment); });
            up.addEventListener('mouseup', () => { this.spin(null); });
            down.addEventListener('mouseup', () => { this.spin(null); });
            up.addEventListener('mouseleave', () => { this.spin(null); });
            down.addEventListener('mouseleave', () => { this.spin(null); });
        }
    }
    /**
     * Spins the time segment based on the direction.
     * @param {Boolean} direction - The direction of the spin.
     * @param {String} segment - The time segment to spin.
     */
    spin(direction, segment) {
        if (direction == null) {
            if (this.timer != null) {
                clearTimeout(this.timer);
                this.timer = null;
            }
        } else {
            let next = +this["h"+segment].innerHTML;
            next = direction ? next + 1 : next - 1;
            if (segment == "hr") {
                if (next > this.maxhr) { next = this.maxhr; }
                if (next < this.minhr) { next = this.minhr; }
            } else {
                if (next > this.maxmin) { next = this.maxmin; }
                if (next < this.minmin) { next = this.minmin; }
            }
            if (next < 10) { next = "0" + next; }
            this["h"+segment].innerHTML = next;
            this.timer = setTimeout(() => { this.spin(direction, segment); }, 100);
        }
    }
    /**
     * Attaches the time picker to the specified input element.
     * @param {Object} instance - The instance of the time picker.
     */
    attach(instance) {
        instance.target.readOnly = true;
        instance.target.setAttribute("autocomplete", "off");
        if (instance["24"] == undefined) { instance["24"] = false; }
        this.show(instance);
    }
    /**
     * Shows the time picker.
     * @param {Object} instance - The instance of the time picker.
     */
    show(instance) {
        this.setfield = instance.target;
        this.setafter = instance.after;
        this.set24 = instance["24"];
        this.minhr = this.set24 ? 0 : 1;
        this.maxhr = this.set24 ? 23 : 12;
        let val = this.setfield.value;
        if (val == "") {
            this.hhr.innerHTML = instance.time.substring(0, 2);
            this.hmin.innerHTML = instance.time.substring(3, 5);
        } else {
            this.hhr.innerHTML = val.substring(0, 2);
            if (this.set24) {
                this.hmin.innerHTML = instance.time.substring(3, 5);
            } else {
                this.hmin.innerHTML = val.substring(3, 5);
            }
        }
        if (this.set24) { this.el.classList.add("tp-24"); }
        else { this.el.classList.remove("tp-24"); }
        this.el.classList.add("show");
    }
    /**
     * Sets the value of the input field to the selected time.
     * @param {Object} e - The event object.
     */
    set(e) {
        if (this.set24) {
            this.setfield.value = this.hhr.innerHTML + ":" + this.hmin.innerHTML;
            if (this.setfield.id == 'time1') {
                this.parent.onChangeTime({target: this.setfield});
            } else {
                this.parent.onChangeTime2({target: this.setfield});
            }
        } else {
            this.setfield.value = this.hhr.innerHTML + ":" + this.hmin.innerHTML;
        }
        this.el.classList.remove("show");
        if (this.setafter) { this.setafter(this.setfield.value); }
    }
     /**
     * Sets the position of the time picker.
     * @param {Number} left - The left position.
     * @param {Number} bottom - The bottom position.
     */
    setPosition(left, bottom) {
        this.el.querySelector('#tp-box').style.left = left;
        this.el.querySelector('#tp-box').style.bottom = bottom;
    }
    /**
     * Closes the time picker.
     * @param {Object} e - The event object.
     */
    close(e) {
        this.el.classList.remove("show");
    }
}