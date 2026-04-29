/** @odoo-module **/
/**It allows users to accept payments in multiple currencies, view
* currency conversion rates, and add payment lines in the selected currency. */
import { PaymentScreen } from "@point_of_sale/app/screens/payment_screen/payment_screen";
import { registry } from "@web/core/registry";
import { onMounted, useState, mount } from "@odoo/owl";
import { patch } from "@web/core/utils/patch";
import { useService } from "@web/core/utils/hooks";
import { usePos } from "@point_of_sale/app/store/pos_hook";


patch(PaymentScreen.prototype, {
    async setup() {
        super.setup();
        this.pos = usePos();
        this.orm = useService("orm");

        this.current_currency = useState({
            rate: 1,
            display_name: '',
            symbol: '',
        });

        this.multi_currency = useState({
            currencies: [],
            usd_val: '',
            name: '',
            total: '',
            symbol: '',
            rate: ''
        });

        // Adding loaded currencies in currency list
        if(this.pos.config.enable_multicurrency){
             const settings = await this.orm.call(
                    'pos.config',
                    'get_config_settings',
                    [this.pos.config.id],
                    {}
                );

             if (settings.length > 0) {
                this.multi_currency.currencies.push(...settings);
            }
        }
    },

    // Showing currencies in settings
    async show_options(event) {
        let isChecked = event.target.checked;

        let multiCurrencyContainer = document.getElementById("multicurrency_container");

        if (multiCurrencyContainer) {
            multiCurrencyContainer.style.display = isChecked ? "block" : "none";
        }
    },

    //Converting the currencies.
    async compute_currency(event){
        const selectedCurrency = event.target.value;
        const selectedId = event.target.selectedOptions[0].id

        let ConvContainer = document.getElementById("conversion_container");
        let multi_cur_input = document.getElementsByClassName("multicurrency_input")[0];

        if (ConvContainer) {
            ConvContainer.style.display = selectedId ? "block" : "none";
        }
        if (multi_cur_input) {
           multi_cur_input.style.border = "1px solid black";

        }

        let totalDiv = document.getElementsByClassName("total")[0];
        let totalText = totalDiv.textContent.trim();
        let totalValue = parseFloat(totalText.replace(/[^0-9.-]+/g, '')); // 74.75


        const currency = await this.orm.call(
                    'pos.config',
                    'get_selected_currency',
                    [selectedId],
                    {}
                );

        this.multi_currency.usd_val = currency[0].usd_val
        this.multi_currency.name = currency[0].name
        this.multi_currency.symbol = currency[0].symbol
        this.multi_currency.rate = currency[0].rate

        this.multi_currency.total = Math.round(currency[0].rate * totalValue * 100) / 100;
    },

    async multi_currency_payment_line(ev){
        if(this.pos.config.enable_multicurrency){
            let amount_val = document.getElementsByClassName("multicurrency_input")[0].value;
            amount_val = parseFloat(amount_val)
            let total_val;
            let remaining_val;
            let total = document.getElementsByClassName("total");
             if(total.length){
                total_val = total[0].innerText
                total_val = parseFloat(total_val.replace(/[^\d.]/g, ''));
            }
            let remaining = document.getElementsByClassName("payment-status-remaining");
             if(remaining.length){
                remaining_val = remaining[0].children[1].innerText
                remaining_val = remaining_val.split(" ")
                remaining_val = parseFloat(remaining_val[1])
            }
             if( total_val > 0 || remaining_val > 0){
                if(amount_val){
                    this.addNewPaymentLine(ev)
                    var update_amount = amount_val / this.multi_currency.rate //entered amount in converted currency
                    await this.selectedPaymentLine.set_amount(update_amount);
                    this.selectedPaymentLine.converted_currency = {
                        'name': this.multi_currency.name,
                        'symbol': this.multi_currency.symbol,
                        'amount': amount_val
                    }
                    this.pos.get_order().converted_currency = {
                        'name': this.multi_currency.name,
                        'symbol': this.multi_currency.symbol,
                        'rate': this.multi_currency.rate,
                        'amount': amount_val,
                        'converted_total': this.multi_currency.total
                    };

                    const el = document.getElementsByClassName("conversion_container")[0];
                    if (el) {
                        el.style.display = 'none';
                    }
                }
                else{
                    const ref = document.getElementsByClassName("multicurrency_input")
                    ref.style.border = "1.5px solid red";
                }
            }
        }
    },

    _updateSelectedPaymentline() {
        super._updateSelectedPaymentline(...arguments);
        if (this.env.pos.config.enable_multicurrency == true) {
            if (this.selectedPaymentLine && this.multi_currency.rate && this.multi_currency.name) {  // ✅ Check rate & name exist
                var change_amount = this.selectedPaymentLine.amount * this.multi_currency.rate;
                this.selectedPaymentLine.converted_currency = {
                    'name': this.multi_currency.name,
                    'symbol': this.multi_currency.symbol,
                    'amount': change_amount
                };
            }
        }
    },

    export_for_printing() {
        const result = super.export_for_printing(...arguments);
        const converted = this.pos.get_order()?.converted_currency;  // ✅ Correct reference
        if (converted) {
            result.converted_currency_amount = converted.amount;
            result.converted_currency_name = converted.name;
            result.converted_currency_symbol = converted.symbol;
            this.currency_amount = converted.amount;
        }
        return result;
    },

    async _finalizeValidation() {
        const paymentLines = this.currentOrder.payment_ids;
        paymentLines.forEach(line => {
            if (line.converted_currency) {  // ✅ Only access if it exists
                line.payment_currency = line.converted_currency.name;
                line.currency_amount = line.converted_currency.amount;
            }
        });
        await super._finalizeValidation();
    },

});
