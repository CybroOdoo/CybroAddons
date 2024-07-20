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
        this.currentInput = '';
        this.currentOperator = '';
        this.result = 0;
        this.state = useState({
            x: 0,
            y: 0,
            isVisible: false
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

    // Display the calculator
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

    async onNumberClick(ev){
        // Handles the click event for number buttons.
        var number = ev.currentTarget.getAttribute('data-key');
        if (number === '.') {
            this.onDecimalClick(ev);
        }
        else {
            this.currentInput += number;
            $(this.rootRef.el.querySelector('.display')).val(this.currentInput);
        }
    }

    async onOperatorClick(ev){
        // Handles the click event for operator buttons.
        var operator = ev.currentTarget.getAttribute('data-key');
        if (this.currentInput !== '') {
            if (this.currentOperator !== '') {
                this.result = this.calculate(this.result, parseFloat(this.currentInput), this.currentOperator);
                $(this.rootRef.el.querySelector('.display')).val(this.result)
            }
            else {
                this.result = parseFloat(this.currentInput);
            }
            this.currentInput = '';
            this.currentOperator = operator;
        }
    }

    async onEqualsClick(){
        // Handles the click event for the equals button.
        if (this.currentInput !== '') {
            this.result = this.calculate(this.result, parseFloat(this.currentInput), this.currentOperator);
            $(this.rootRef.el.querySelector('.display')).val(this.result);
            this.currentInput = this.result.toString();
            this.currentOperator = '';
        }
    }

    async onClearClick(){
        // Handles the click event for the Clear button.
        this.result = 0;
        this.currentInput = '';
        this.currentOperator = '';
        $(this.rootRef.el.querySelector('.display')).val('');
    }

    async onToggleSignClick(){
        // Handles the click event for the sign button.
        if (this.currentInput !== '') {
            // Check if the current input is a negative number
            if (this.currentInput[0] === '-') {
                // Remove the negative sign to make it positive
                this.currentInput = this.currentInput.substring(1);
            } else {
                // Add a negative sign to make it negative
                this.currentInput = '-' + this.currentInput;
            }
            $(this.rootRef.el.querySelector('.display')).val(this.currentInput);
        }
    }
    async onDecimalClick(ev){
        // Handles the click event for the decimal point toggle button
        var decimal = ev.currentTarget.getAttribute('data-key');
        if (this.currentInput.indexOf('.') === -1) {
            this.currentInput += decimal;
            $(this.rootRef.el.querySelector('.display')).val(this.currentInput);
        }
    }
    calculate(num1, num2, operator) {
        // Performs arithmetic calculations based on the provided operator.
        switch (operator) {
            case '+':
                return num1 + num2;
            case '-':
                return num1 - num2;
            case '*':
                return num1 * num2;
            case '/':
                return num1 / num2;
            case '%':
                return (num1 / 100) * num2;
            default:
                return num2;
        }
    }
}

Calculator.template = 'CalculatorTool';
Calculator.components = { Dropdown, DropdownItem };

export const calculator = {
    Component: Calculator,
};

registry.category('systray').add('Calculator', calculator);