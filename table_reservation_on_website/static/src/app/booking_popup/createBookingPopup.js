/**@odoo-module **/
import { AbstractAwaitablePopup } from "@point_of_sale/app/popup/abstract_awaitable_popup";
import { ConfirmPopup } from "@point_of_sale/app/utils/confirm_popup/confirm_popup";
import { ErrorPopup } from "@point_of_sale/app/errors/popups/error_popup";
import { usePos } from "@point_of_sale/app/store/pos_hook";
import { useService } from "@web/core/utils/hooks";
import { useState } from "@odoo/owl";
import { _t } from "@web/core/l10n/translation";

export class createBookingPopup extends AbstractAwaitablePopup {
    setup() {
        super.setup();
        this.orm = useService('orm');
        this.pos = usePos();
        this.popup = useService("popup");
        this.state = useState({
            customers: this.env.services.pos.partners,
            partner: '',
            floors: this.env.services.pos.floors,
            floor: '',
            date: '',
            start_time: '',
            end_time: '',
            tables: [],
            table: '',
            amount: '',
            lead_time: '',
            Table: '',
            table_details_header: false,
        });
    }
    // Filter tables according to floor selected
    async onSelectFloor(ev) {
        this.state.amount = ''
        const selectedFloorText = ev.target.options[ev.target.selectedIndex].text;
        if (ev.target.options[ev.target.selectedIndex].text != 'Select Floor'){
            var table_data = []
            this.state.table_details_header = true
            this.state.Table = ''
            var floor_id = this.state.floor
            var date = this.state.date
            var start_time = this.state.start_time
            var end_time = this.state.end_time
            if (start_time > end_time){
                this.popup.add(ConfirmPopup, {
                    title: _t("Error"),
                    body: _t("Start time can't be greater than end time."),
                });
            }
            if ((start_time && end_time) && (start_time === end_time)) {
                this.popup.add(ConfirmPopup, {
                    title: _t("Error"),
                    body: _t("Start time and end time can't be same."),
                });
            }
            if (date && start_time && end_time){
                var table_data = await this.orm.call('table.reservation', 'get_table_details', [
                    floor_id, date, start_time, end_time])
                this.state.tables = table_data
            }
        }
    }
    // To Check selected date is valid one
    async onChangeDate() {
        var selectedDate = new Date(this.state.date);
        const currentDate = new Date();
        if (selectedDate < currentDate.setHours(0, 0, 0, 0)){
            this.popup.add(ErrorPopup, {
                title: _t("Invalid Date"),
                body: _t("Please select a valid date."),
            }).then(() => {
                this.state.date = null;
            });
        }
        this.onChangeTime()
    }
    // To check selected time is not past one
    onChangeTime() {
        let now = new Date();
        let currentHours = now.getHours().toString().padStart(2, '0');
        let currentMinutes = now.getMinutes().toString().padStart(2, '0');
        let currentTime = `${currentHours}:${currentMinutes}`;
        // Get the current date
        const currentDate = new Date();
        const year = currentDate.getFullYear();
        const month = String(currentDate.getMonth() + 1).padStart(2, '0'); // Months are zero-based
        const day = String(currentDate.getDate()).padStart(2, '0');
        // Format the date as YYYY-MM-DD
        const formattedDate = `${year}-${month}-${day}`;
        if (this.state.date == formattedDate){
            if (this.state.start_time && this.state.start_time < currentTime) {
                 this.popup.add(ErrorPopup, {
                    title: _t("Invalid Time"),
                    body: _t("You can't select past time."),
                 }).then(() => {
                    this.state.start_time = null;
                 });
            }
            else if (this.state.end_time && this.state.end_time < currentTime) {
                this.popup.add(ErrorPopup, {
                    title: _t("Invalid Time"),
                    body: _t("You can't select past time."),
                 }).then(() => {
                    this.state.end_time = null;
                });
            }
        }
        // Check start time is not greater than end time
        if ((this.state.start_time && this.state.end_time) && (this.state.start_time > this.state.end_time)){
            this.popup.add(ConfirmPopup, {
                title: _t("Error"),
                body: _t("Start time can't be greater than end time."),
            }).then(() => {
                this.state.start_time = null;
                this.state.end_time = null;
            });
        }
        // Check start and end time not same
        if ((this.state.start_time && this.state.end_time) && (this.state.start_time === this.state.end_time)) {
            this.popup.add(ConfirmPopup, {
                title: _t("Error"),
                body: _t("Start time and end time can't be same."),
            }).then(() => {
                this.state.start_time = null;
                this.state.end_time = null;
            });
        }
    }
    // Select tables for booking
    async onSelectTable(ev) {
        var table_div = ev.target.closest('.card_table');
        var tableId = table_div.getAttribute('data-id');
        if (table_div.style.backgroundColor === 'green') {
            table_div.style.backgroundColor = '#96ccd5';
            this.state.Table = this.state.Table.split(',').filter(id => id !== tableId).join(',');
        } else {
            table_div.style.backgroundColor = 'green';
            if (this.state.Table.length > 0) {
                this.state.Table += ',' + tableId;
            } else {
                this.state.Table = tableId;
            }
        }
        if (this.state.floor && this.state.Table !== '') {
            var reservation_amount = await this.orm.call('table.reservation', 'get_reservation_amount', [this.state.Table]);
            this.state.amount = reservation_amount;
        } else {
            this.state.amount = 0;
        }
    }
    // Create new reservation
    createReservation() {
        this.onChangeTime()
        if (this.state.partner && this.state.date && this.state.start_time && this.state.end_time
            && this.state.floor && this.state.Table) {
                this.orm.call('table.reservation', 'create_table_reservation', [
                this.state.Table, this.state.date, this.state.start_time, this.state.end_time,
                this.state.partner, this.state.lead_time, this.state.floor])
                location.reload()
        }
        else{
            this.popup.add(ErrorPopup, {
                title: _t("Alert"),
                body: _t("Please fill all the required details."),
            });
        }
    }
    // Create new reservation and make payments if reservation charge enabled
    async createReservationPayment(ev) {
        this.onChangeTime()
        if (this.state.start_time > this.state.end_time){
            this.popup.add(ConfirmPopup, {
                title: _t("Error"),
                body: _t("Start time can't be greater than end time."),
            });
        }
        if ((this.state.start_time && this.state.end_time) && (this.state.start_time === this.state.end_time)) {
            this.popup.add(ConfirmPopup, {
                title: _t("Error"),
                body: _t("Start time and end time can't be same."),
            });
        }
        if (this.state.partner && this.state.partner != 'Select Customer') {
            if (this.state.date && this.state.start_time && this.state.end_time
                && this.state.floor && this.state.Table) {
                    var data = await this.orm.call('table.reservation', 'create_table_reservation', [
                        this.state.Table, this.state.date, this.state.start_time, this.state.end_time,
                        this.state.partner, this.state.lead_time, this.state.floor, this.pos.get_order().name])
                this.cancel();
                this.pos.showScreen('ProductScreen');
                var product = this.pos.db.product_by_id[data]
                product['lst_price'] = this.state.amount
                this.pos.get_order().set_partner(this.pos.db.partner_by_id[parseInt(this.state.partner)])
                this.pos.get_order().add_product(product, {
                    quantity: 1,
                });
            }
            else{
                this.popup.add(ErrorPopup, {
                    title: _t("Alert"),
                    body: _t("Please fill all the required details."),
                });
            }
        }
        else {
            this.popup.add(ErrorPopup, {
                    title: _t("Alert"),
                    body: _t("Please fill all the required details."),
            });
        }
    }
}
createBookingPopup.template = "createBookingPopup";
