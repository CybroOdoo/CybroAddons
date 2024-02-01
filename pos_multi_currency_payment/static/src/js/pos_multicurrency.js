/**It allows users to accept payments in multiple currencies, view
 * currency conversion rates, and add payment lines in the selected currency. */
odoo.define('POS_multi_currency.MultiCurrency', function(require) {
    "use strict";
    const PaymentScreen = require('point_of_sale.PaymentScreen');
    const { useListener } = require("@web/core/utils/hooks");
    const Registries = require('point_of_sale.Registries');
    var { Payment } = require('point_of_sale.models')
    var rpc = require('web.rpc');
    var current_currency,currency_id;
    const {onMounted, useState , mount } = owl;
    const PaymentScreenMultiCurrency = PaymentScreen => class extends PaymentScreen {
        setup() {
            super.setup();
            useListener('multi-payment-line', this.multi_currency_payment_line);
            var currency = []
            onMounted(this.enable_multi_currency)
            //Adding loaded currencies in currency list
            currency.push(this.env.pos.currency.currency_params)
            this.multi_currency = useState({
                'currencies': currency
            });
        }
        enable_multi_currency(){
            if(this.env.pos.config.enable_multicurrency ==  false){
                $('.pos_multicurrency').css('display','none')
            }
        }
        //Showing currencies in settings
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
        }
        //Converting the currencies.
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
                var total_array = initial_total.split(" ");
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
        }
        //Adding entered currency amount in payment line.
        async multi_currency_payment_line(ev){
            var amount_val = parseFloat($('.multicurrency_input').val())
            var total_val
            var remaining_val
            if($('.total').length){
                total_val = $('.total')[0].innerText
                total_val = total_val.split(" ")
                total_val = parseFloat(total_val[1])
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
        //For deleting payment line.
        deletePaymentLine(event) {
            super.deletePaymentLine(...arguments);
            $('.currecy_list')[0].selectedIndex = 0
            $('.conversion_container').css({'display':'none'})
        }
        //Function for updating the payment line dynamically
        _updateSelectedPaymentline(){
                       super._updateSelectedPaymentline(...arguments);
                       var  change_amount=this.selectedPaymentLine.amount*current_currency.rate
                       this.selectedPaymentLine.converted_currency = {
                            'name': current_currency.display_name,
                            'symbol': current_currency.symbol,
                            'amount': change_amount
                    }
        }
    };
    Registries.Component.extend(PaymentScreen, PaymentScreenMultiCurrency);
    return PaymentScreen;
});
