/** @odoo-module **/
import { PaymentScreen } from "@point_of_sale/app/screens/payment_screen/payment_screen";
import { registry } from "@web/core/registry";
import { onMounted, useState, mount } from "@odoo/owl";
import { patch } from "@web/core/utils/patch";
import { useService } from "@web/core/utils/hooks";
import { usePos } from "@point_of_sale/app/store/pos_hook";
var current_currency,currency_id
patch(PaymentScreen.prototype, {
    setup(){
    super.setup();
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

    //            useListener('multi-payment-line', this.multi_currency_payment_line);
    this.env.bus.addEventListener('multi-payment-line', this.multi_currency_payment_line.bind(this));
    var currency=[]
    onMounted(() => {
        this.multi_currency.currencies = currency;
        this.enable_multi_currency();
    });
currency.push(this.pos.currency.currency_params)

    },

    enable_multi_currency(){
            if(this.pos.config.enable_multicurrency ==  false){
                $('.pos_multicurrency').css('display','none')
            }
    },

    show_options(){
            if($('.multicurrency_container')[0].style.display == 'none'){
                $('.multicurrency_container').css({'display':'flex','flex-direction':'column','align-items': 'center'})
                for (let i = 0, len = this.multi_currency.currencies[0].length; i < len; i++){
                    $('.currecy_list').append("<option id="+this.multi_currency.currencies[0][i].id+">"+this.multi_currency.currencies[0][i].display_name+"</option")
                }
            }else{
                $('.currecy_list').empty()
                $('.multicurrency_container').css('display','none')
            }
    },
    compute_currency(ev){
            currency_id = $('.currecy_list').find('option:selected')[0].id
            if(currency_id){
                $('.conversion_container').css({'display':'block','text-align': 'center'})
                $('.multicurrency_input').css({'border':'1px solid black'})
                current_currency = this.multi_currency.currencies[0].find(item => item.id === parseInt(currency_id));
                var initial_total
                if ($('.total').length > 0 ){
                    initial_total = $('.total')[0].innerText

                }else{
                    initial_total = $('.payment-status-remaining')[0].children[1].innerText
                }
                var total_array = initial_total.split(/\s| /);
                var total_value = parseFloat(total_array[1])
                $('.rate_string')[0].innerText = current_currency.rate_string
                //Total in converted curency
                var display_total = current_currency.rate * total_value
                if(display_total == 0){
                    $('.conversion_container').css({'display':'none'})
                }else{
                    $('.total_amount')[0].innerText = display_total
                }
            }else{
                $('.conversion_container').css({'display':'none'})
            }
        },
        //Adding entered currency amount in payment line.
    async multi_currency_payment_line(ev){
        if(this.pos.config.enable_multicurrency ==  true){
            var amount_val = parseFloat($('.multicurrency_input').val())
            let total_val;
            let remaining_val;
            let total = document.getElementsByClassName("total");
            if($('.total').length){
               total_val = total[0].innerText
                total_val = parseFloat(total_val.replace(/[^\d.]/g, ''));
            }

            if($('.payment-status-remaining').length){
                remaining_val = $('.payment-status-remaining')[0].children[1].innerText
                remaining_val = remaining_val.split(" ")
                remaining_val = parseFloat(remaining_val[1])
            }
            if( total_val > 0 || remaining_val > 0){
                if(amount_val){
                    this.addNewPaymentLine(ev)
                    var update_amount = amount_val / current_currency.rate //entered amount in converted currency
                    await this.selectedPaymentLine.set_amount(update_amount);
                    this.selectedPaymentLine.converted_currency = {
                            'name': current_currency.display_name,
                            'symbol': current_currency.symbol,
                            'amount': amount_val
                    }
                    $('.multicurrency_input').val('')
                    $('.conversion_container').css({'display':'none'})
                    $('.currecy_list')[0].selectedIndex = 0
                }
                else{
                    $('.multicurrency_input').css({'border':'1.5px solid red'})
                }
            }
            }

        },
        //For deleting payment line.
    deletePaymentLine(event) {
        super.deletePaymentLine(...arguments);
        $('.currecy_list')[0].selectedIndex = 0
        $('.conversion_container').css({'display':'none'})
    },
    //Function for updating the payment line dynamically
    _updateSelectedPaymentline(){

            super._updateSelectedPaymentline(...arguments);
            if(this.env.pos.config.enable_multicurrency ==  true){
                if (this.selectedPaymentLine) {
                    var change_amount = this.selectedPaymentLine.amount * current_currency.rate;
                    this.selectedPaymentLine.converted_currency = {
                        'name': current_currency.display_name,
                        'symbol': current_currency.symbol,
                        'amount': change_amount
                    };
                }
            }
        },
        export_for_printing() {
        const result = super.export_for_printing(...arguments);
        if(this.converted_currency){
            result.converted_currency_amount = this.converted_currency.amount
            result.converted_currency_name = this.converted_currency.name
            result.converted_currency_symbol = this.converted_currency.symbol
            this.currency_amount = this.converted_currency.amount
            }
            return result;
        },

        async _finalizeValidation() {
            const paymentLines = this.currentOrder.paymentlines;
            paymentLines.forEach( line => {
                if (line.converted_currency) {
                console.log("oooo: ", line)
                line.payment_currency = line.converted_currency.name;
                line.currency_amount = line.converted_currency.amount;
                line.currency_symbol = line.converted_currency.symbol;
            }
            });
            await super._finalizeValidation();
        },
    });
