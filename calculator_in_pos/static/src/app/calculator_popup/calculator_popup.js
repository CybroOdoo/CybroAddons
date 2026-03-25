/**@odoo-module **/
import { Component, useRef, useState } from "@odoo/owl";
import { Dialog } from "@web/core/dialog/dialog";


export class CalculatorPopup extends Component {
    static template = "calculator_in_pos.CalculatorPopup";
    static components = { Dialog };
    setup() {
        super.setup();
        this.rootRef = useRef('root');
        this.state = useState({
            currentInput: '',
            currentOperator: '',
            result: 0,
            isVisible: false,
            display: ''
        });
    }

    static props = {
        title: String,
        close: Function
    };

    static defaultProps = {};
        onclick_calc_icon() {
        this.state.isVisible = !this.state.isVisible;
    }

    onNumberClick(ev) {
        const number = ev.currentTarget.getAttribute('data-key');
        if (number === '.') {
            this.onDecimalClick(ev);
        } else {
            this.state.currentInput += number;
            this.state.display = this.state.currentInput;
        }
    }

    onOperatorClick(ev) {
        const operator = ev.currentTarget.getAttribute('data-key');
        if (this.state.currentInput !== '') {
            if (this.state.currentOperator !== '') {
                this.state.result = this.calculate(this.state.result, parseFloat(this.state.currentInput), this.state.currentOperator);
                this.state.display = this.state.result.toString();
            } else {
                this.state.result = parseFloat(this.state.currentInput);
            }
            this.state.currentInput = '';
            this.state.currentOperator = operator;
        }
    }

    onEqualsClick() {
        if (this.state.currentInput !== '') {
            this.state.result = this.calculate(this.state.result, parseFloat(this.state.currentInput), this.state.currentOperator);
            this.state.display = this.state.result.toString();
            this.state.currentInput = this.state.result.toString();
            this.state.currentOperator = '';
        }
    }

    onClearClick() {
        this.state.result = 0;
        this.state.currentInput = '';
        this.state.currentOperator = '';
        this.state.display = '';
    }

    onToggleSignClick() {
        if (this.state.currentInput !== '') {
            if (this.state.currentInput[0] === '-') {
                this.state.currentInput = this.state.currentInput.substring(1);
            } else {
                this.state.currentInput = '-' + this.state.currentInput;
            }
            this.state.display = this.state.currentInput;
        }
    }

    onDecimalClick(ev) {
        const decimal = ev.currentTarget.getAttribute('data-key');
        if (this.state.currentInput.indexOf('.') === -1) {
            this.state.currentInput += decimal;
            this.state.display = this.state.currentInput;
        }
    }

    calculate(num1, num2, operator) {
        switch (operator) {
            case '+': return num1 + num2;
            case '-': return num1 - num2;
            case '*': return num1 * num2;
            case '/': return num1 / num2;
            case '%': return (num1 / 100) * num2;
            default: return num2;
        }
    }
}
