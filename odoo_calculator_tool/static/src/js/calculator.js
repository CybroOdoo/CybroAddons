/** @odoo-module **/
import SystrayMenu from 'web.SystrayMenu';
var Widget = require('web.Widget');
var CalculatorTool = Widget.extend({
    template: 'CalculatorTool',
    events: {
        // Add your calculator specific events
        'click .number': 'onNumberClick',
        'click .operator': 'onOperatorClick',
        'click .equals': 'onEqualsClick',
        'click .clear': 'onClearClick',
        'click .toggle-sign': 'onToggleSignClick',
        'click .decimal': 'onDecimalClick',
    },
    init: function (parent) {
        this._super(parent);
        this.currentInput = '';
        this.currentOperator = '';
        this.result = 0;
    },
    start: function () {
        this.$('.calc_dropdown-toggle').click(this._onDropdownToggleClick.bind(this));
        this.$('.draggable-tool').draggable();
        return this._super.apply(this, arguments);
    },
    onNumberClick: function (ev) {
    // Handles the click event for number buttons.
        var number = ev.currentTarget.getAttribute('data-key');
        if (number === '.') {
            this.onDecimalClick(ev);
        }
        else {
            this.currentInput += number;
            this.$('.display').val(this.currentInput);
        }
    },
    onOperatorClick: function (ev) {
    // Handles the click event for operator buttons.
        var operator = ev.currentTarget.getAttribute('data-key');
        if (this.currentInput !== '') {
            if (this.currentOperator !== '') {
                this.result = this.calculate(this.result, parseFloat(this.currentInput), this.currentOperator);
                this.$('.display').val(this.result);
            }
            else {
                this.result = parseFloat(this.currentInput);
            }
            this.currentInput = '';
            this.currentOperator = operator;
        }
    },
    onEqualsClick: function () {
    // Handles the click event for the equals button.
        if (this.currentInput !== '') {
            this.result = this.calculate(this.result, parseFloat(this.currentInput), this.currentOperator);
            this.$('.display').val(this.result);
            this.currentInput = this.result.toString();
            this.currentOperator = '';
        }
    },
    onClearClick: function () {
    // Handles the click event for the Clear button.
        this.result = 0;
        this.currentInput = '';
        this.currentOperator = '';
        this.$('.display').val('');
    },
    calculate: function (num1, num2, operator) {
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
    },
    onDecimalClick: function (ev) {
    // Handles the click event for the decimal point toggle button
        var decimal = ev.currentTarget.getAttribute('data-key');
        if (this.currentInput.indexOf('.') === -1) {
            this.currentInput += decimal;
            this.$('.display').val(this.currentInput);
        }
    },
    onToggleSignClick: function () {
        if (this.currentInput !== '') {
            // Check if the current input is a negative number
            if (this.currentInput[0] === '-') {
                // Remove the negative sign to make it positive
                this.currentInput = this.currentInput.substring(1);
            } else {
                // Add a negative sign to make it negative
                this.currentInput = '-' + this.currentInput;
            }
            this.$('.display').val(this.currentInput);
        }
    },
    _onDropdownToggleClick: function () {
    // Handles the click event for the dropdown toggle button.
        var $dropdownMenu = this.$el.find('.calc_dropdown-menu');
        $dropdownMenu.toggle();
    },
});

SystrayMenu.Items.push(CalculatorTool);
export default CalculatorTool;
