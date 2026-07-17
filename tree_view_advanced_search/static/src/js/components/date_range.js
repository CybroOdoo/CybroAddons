/** @odoo-module */
import { Component, useState } from "@odoo/owl";
import { _t } from "@web/core/l10n/translation";
import { DateTimeInput } from "@web/core/datetime/datetime_input";
import { serializeDate, deserializeDate } from "@web/core/l10n/dates";

export class DateRange extends Component {
    static template = "tree_view_advanced_search.DateRange";
    static components = { DateTimeInput };
    static props = {
        onFromToChanged: Function,
    };

    setup() {
        this.state = useState({
            from: false,
            to: false,
        });
        this.fromPlaceholder = _t("Date From");
        this.toPlaceholder = _t("Date To");
    }

    onDateFromChanged(dateFrom) {
        this.state.from = dateFrom && serializeDate(dateFrom.startOf("day"));
        this.props.onFromToChanged({
            from: this.state.from,
            to: this.state.to,
        });
    }

    onDateToChanged(dateTo) {
        this.state.to = dateTo && serializeDate(dateTo.endOf("day"));
        this.props.onFromToChanged({
            from: this.state.from,
            to: this.state.to,
        });
    }

    get dateFrom() {
        return this.state.from ? deserializeDate(this.state.from) : null;
    }

    get dateTo() {
        return this.state.to ? deserializeDate(this.state.to) : null;
    }
}
