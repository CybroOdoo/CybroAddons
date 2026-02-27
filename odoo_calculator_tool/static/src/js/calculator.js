/** @odoo-module **/
import { Dropdown } from '@web/core/dropdown/dropdown';
import { DropdownItem } from '@web/core/dropdown/dropdown_item';
import { registry } from '@web/core/registry';
import { Component } from '@odoo/owl';
import { useRef, useState, onMounted, onWillUnmount } from "@odoo/owl";

export class Calculator extends Component {
    setup() {
        super.setup();
        this.rootRef = useRef('root');
        this.state = useState({
            currentInput: '',
            currentOperator: '',
            result: 0,
            x: 0,
            y: 0,
            isVisible: false,
            display: ''
        });

        this.dragStartX = 0;
        this.dragStartY = 0;

        onMounted(() => {
            document.addEventListener('mousemove', this.onDragging);
            document.addEventListener('mouseup', this.stopDragging);
        });

        onWillUnmount(() => {
            document.removeEventListener('mousemove', this.onDragging);
            document.removeEventListener('mouseup', this.stopDragging);
        });
    }

    onclick_calc_icon() {
        this.state.isVisible = !this.state.isVisible;
    }

    startDragging(ev) {
        this.isDragging = true;
        this.dragStartX = ev.clientX - this.state.x;
        this.dragStartY = ev.clientY - this.state.y;
    }

    onDragging = (ev) => {
        if (this.isDragging) {
            this.state.x = ev.clientX - this.dragStartX;
            this.state.y = ev.clientY - this.dragStartY;
        }
    }

    stopDragging = () => {
        this.isDragging = false;
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

Calculator.template = 'CalculatorTool';
Calculator.components = { Dropdown, DropdownItem };

export const calculator = {
    Component: Calculator,
};

registry.category('systray').add('Calculator', calculator);
