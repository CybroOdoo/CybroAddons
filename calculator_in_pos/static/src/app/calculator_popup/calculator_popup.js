/** @odoo-module **/
import { AbstractAwaitablePopup } from "@point_of_sale/app/popup/abstract_awaitable_popup";
import { _t } from "@web/core/l10n/translation";
import { useState } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";
import { Numpad } from "@point_of_sale/app/generic_components/numpad/numpad";

const INPUT_KEYS = ['x', '/', '%', '+', '-', '=', 'Delete', '⌫']

/* This class represents calculator popup in product screen. */
export class CalculatorPopup extends AbstractAwaitablePopup {
    static template = "CalculatorPopup";
    static components = { Numpad };
    static defaultProps = {
        cancelText: _t("Close"),
        title: _t("Calculator"),
        getInputBufferReminder: () => false,
    };
    /* Initializes the component and sets up necessary dependencies. */
    setup() {
        super.setup();
        let startingBuffer = "";
        if (typeof this.props.startingValue === "number" && this.props.startingValue > 0) {
            startingBuffer = this.props.startingValue
                .toFixed(this.props.nbrDecimal)
                .toString()
                .replace(".", this.decimalSeparator);
        }
        this.state = useState({
            buffer: startingBuffer,
        });
        this.numberBuffer = useService("number_buffer");
        this.numberBuffer.use({
            triggerAtEnter: () => this.confirm(),
            triggerAtEscape: () => this.cancel(),
            state: this.state,
        });
        this.orm = useService("orm");
    }
    /* Load buttons in Calculator popup. */
    getNumpadButtonsPOS() {
        return [
            { value: "1" , class:"input-btn"},
            { value: "2" , class:"input-btn"},
            { value: "3" , class:"input-btn"},
            { value: "4" , class:"input-btn"},
            { value: "5" , class:"input-btn"},
            { value: "6" , class:"input-btn"},
            { value: "7" , class:"input-btn"},
            { value: "8" , class:"input-btn"},
            { value: "9" , class:"input-btn"},
            { value: "0" , class:"input-btn"},
            { value: "Delete", text:"AC", class:"operator-btn"},
            { text:"+" , class:"operator-btn"},
            { text: "-", class:"operator-btn"},
            { value: this.env.services.localization.decimalPoint, class:"operator-btn"},
            { value: "x", text: "x", class:"operator-btn"},
            { text: "⌫", class:"backspace-btn"},
            { value: "/", text:"/" , class:"operator-btn"},
            { value: "%", text: "%", class:"operator-btn"},
            { value: "=", text: "=", class:"equal-btn"},
        ];
    }
    /*
    * This method retrieves the current state of the input buffer. If the buffer
    * is null, an empty string is returned.
    */
    get inputBuffer() {
        if (this.state.buffer === null) {
            return "";
        }
        else {
            return this.state.buffer;
        }
    }
    /* Determine if the current device is in a mobile view. */
    isMobile() {
        return window.innerWidth <= 768;
    }
    /**
    * Handles numpad button click event.
    *
    * It performs different actions based on the clicked button including
    * clearing the buffer, backspacing, performing calculations, and appending
    * characters to the buffer.
    */
    onClickNumpad(ev) {
        if (INPUT_KEYS.includes(ev.target.innerText)){
            console.log('input keys')
            if (ev.target.innerText === 'Clear') {
                this.state.buffer = '';
            } else if (ev.target.innerText === '⌫') {
                this.state.buffer = this.state.buffer.slice(0,-1);
            } else if (ev.target.innerText === '=') {
                console.log('key', ev.target.innerText)
                var data = this.state.buffer.replace(/x/g, "*");
                var self = this;
                this.state.buffer = this.orm.call('pos.calculator', 'calculations', [false, data]
                ).then(function (result) {
                    self.state.buffer = result;
                });
            } else {
                if (this.state.buffer === null || this.state.buffer === '') {
                    if (ev.target.innerText === '+' ||ev.target.innerText === '-') {
                        this.state.buffer = ev.target.innerText;
                        console.log('1')
                    }
                } else if (/[0-9]/g.test(this.state.buffer.slice(-1)) === true) {
                    console.log('this.state.buffer', this.state.buffer)
                    console.log('this.state.inner', ev.target.innerText)
                    this.state.buffer = this.state.buffer + ev.target.innerText;
                    console.log('2')
                } else {
                    if (/[0-9]/g.test(this.state.buffer.slice(-2)) === true){
                        console.log('3-res', this.state.buffer.slice(0,-1))
                        this.state.buffer = this.state.buffer.slice(0,-1) + ev.target.innerText;
                        console.log('3')
                    } else {
                        this.state.buffer = this.state.buffer.slice(0,-2) + ev.target.innerText;
                        console.log('4')
                    }
                }
            }
        }
    }
}
