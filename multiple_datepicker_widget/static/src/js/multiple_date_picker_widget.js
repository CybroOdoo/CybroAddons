/** @odoo-module **/
import { registry } from "@web/core/registry";
import time from 'web.time';
var translation = require('web.translation');
var _t = translation._t;
const { Component,useRef, useState} = owl;

export class DomainSelectorTextField extends Component {
    static template = 'FieldDateMultipleDate'

    setup(){
        super.setup();
        this.input = useRef('inputdate')
        this.state = useState({
            date: this.props.value
        })
    }

    _onSelectDateField(ev){

        var dateFormat = time.getLangDateFormat();

        if (dateFormat.includes('MMMM')){
          var dates = dateFormat.toLowerCase()
          var result = dates.replace(/mmmm/g, 'MM');
          console.log(result, 'res1')
          dateFormat = result
        }

        else if (dateFormat.includes('MMM')) {
          var dates = dateFormat.toLowerCase()
          var result = dates.replace(/mmm/g, 'M');
          console.log(result, 'res2')

          dateFormat = result
        }

        else if(dateFormat.includes('ddd')){
          var dates =new dateFormat.toLowerCase()
          var result = new dates.replace(/ddd/g, 'DD');
          console.log(result, 'res3')

          dateFormat = result
        }

        else {
            dateFormat = dateFormat.toLowerCase()
            console.log(dateFormat, 'res4')
        }
        console.log($(this.input.el), 'eee')
        if (this.input.el){
            $(this.input.el).datepicker({
                multidate: true,
                format: dateFormat
            }).on('changeDate',async (ev) => await this.onSelectDate(ev, dateFormat)).trigger('focus');
        }
    }

    async onSelectDate(ev, dateFormat) {
        if (ev.dates.length === 0) {
            this.state.date = "";
            await this.props.update(this.state.date);

            $(this.input.el).val('');
            return;
        }

        let dateList = ev.dates.map(date => moment(date).format(this.convertToMomentFormat(dateFormat)));

        this.state.date = [...new Set(dateList)].join(',');

        await this.props.update(this.state.date);
    }


    convertToMomentFormat(format) {
        return format.replace(/d{1,2}/g, 'DD')
                 .replace(/m{1,2}/g, 'MM')
                 .replace(/y{2,4}/g, 'YYYY');
    }
}
registry.category("fields").add("multiple_datepicker", DomainSelectorTextField);
