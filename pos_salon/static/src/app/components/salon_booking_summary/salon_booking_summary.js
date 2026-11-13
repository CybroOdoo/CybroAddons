import { Component } from "@odoo/owl";
import { usePos } from "@point_of_sale/app/hooks/pos_hook";
import { formatSalonAmount } from "@pos_salon/app/utils/salon_currency";

export class SalonBookingSummary extends Component {
    static template = "pos_salon.SalonBookingSummary";
    static props = [
        "customerName",
        "customerPhone?",
        "specialistName?",
        "dateLabel?",
        "showTime?",
        "lines",
        "amenities?",
        "total",
    ];

    setup() {
        this.pos = usePos();
    }

    formatAmount(value) {
        return formatSalonAmount(this.pos, value);
    }
}