/** @odoo-module */
import { Component, useState, onWillUpdateProps } from "@odoo/owl";
import { _t } from "@web/core/l10n/translation";
import { DateTimeInput } from "@web/core/datetime/datetime_input";
import { serializeDate, deserializeDate } from "@web/core/l10n/dates";

export class DateRange extends Component {
    static template = "DateRange";
    static components = { DateTimeInput };
    static props = {
        onFromToChanged: Function,
        value: { type: Object, optional: true },
    };
    fromPlaceholder = _t("Date From");
    toPlaceholder = _t("Date To");

    setup(){
        this.state = useState({
            from: (this.props.value && this.props.value.from) || false,
            to: (this.props.value && this.props.value.to) || false,
        });

        onWillUpdateProps((nextProps) => {
            if (nextProps.value) {
                this.state.from = nextProps.value.from || false;
                this.state.to = nextProps.value.to || false;
            } else {
                this.state.from = false;
                this.state.to = false;
            }
        });
    }
    onDateFromChanged(dateFrom) {
        const fromVal = dateFrom ? serializeDate(dateFrom.startOf("day")) : false;
        this.state.from = fromVal;
        this.props.onFromToChanged({
            from: fromVal,
            to: this.state.to,
        });
    }
    onDateToChanged(dateTo) {
        const toVal = dateTo ? serializeDate(dateTo.endOf("day")) : false;
        this.state.to = toVal;
        this.props.onFromToChanged({
            from: this.state.from,
            to: toVal,
        });
    }
    get dateFrom() {
        return this.state.from && deserializeDate(this.state.from);
    }
    get dateTo() {
        return this.state.to && deserializeDate(this.state.to);
    }
}
