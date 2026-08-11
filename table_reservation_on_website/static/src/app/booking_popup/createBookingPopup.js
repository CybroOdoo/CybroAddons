/**@odoo-module **/
import { AlertDialog, ConfirmationDialog } from "@web/core/confirmation_dialog/confirmation_dialog";
import { usePos } from "@point_of_sale/app/store/pos_hook";
import { Component, useState } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";
import { _t } from "@web/core/l10n/translation";
import { Dialog } from "@web/core/dialog/dialog";

export class createBookingPopup extends Component {
    static components = { Dialog };
    static props = {
        close: Function,
        title: String,
        getPayload: { type: Function, optional: true },
        data: { type: Object, optional: true },
    };
    setup() {
        super.setup();
        this.orm = useService('orm');
        this.pos = usePos();
        this.dialog = useService("dialog");
        this.state = useState({
            customers: this.pos.models["res.partner"].getAll(),
            partner: '',
            floors: this.pos.models["restaurant.floor"].getAll(),
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
                this.dialog.add(AlertDialog, {
                    title: _t("Error"),
                    body: _t("Start time can't be greater than end time."),
                });
            }
            if ((start_time && end_time) && (start_time === end_time)) {
                this.dialog.add(AlertDialog, {
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
        if (!this.state.date || isNaN(new Date(this.state.date).getTime()) || new Date(this.state.date).getFullYear() < 1000) {
            return;
        }
        var selectedDate = new Date(this.state.date);
        if (selectedDate.getFullYear() > 9999) {
            this.dialog.add(AlertDialog, {
                title: _t("Invalid Date"),
                body: _t("Invalid Year"),
                confirm: () => {
                    this.state.date = null;
                },
            });
            return;
        }
        const currentDate = new Date();
        if (selectedDate < currentDate.setHours(0, 0, 0, 0)){
            this.dialog.add(AlertDialog, {
                title: _t("Invalid Date"),
                body: _t("Please select a valid date."),
                confirm: () => {
                    this.state.date = null;
                },
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
                 this.dialog.add(AlertDialog, {
                    title: _t("Invalid Time"),
                    body: _t("You can't select past time."),
                    confirm: () => {
                        this.state.start_time = null;
                    },
                 });
            }
            else if (this.state.end_time && this.state.end_time < currentTime) {
                this.dialog.add(AlertDialog, {
                    title: _t("Invalid Time"),
                    body: _t("You can't select past time."),
                    confirm: () => {
                        this.state.end_time = null;
                    },
                });
            }
        }
        // Check start time is not greater than end time
        if ((this.state.start_time && this.state.end_time) && (this.state.start_time > this.state.end_time)){
            this.dialog.add(AlertDialog, {
                title: _t("Error"),
                body: _t("Start time can't be greater than end time."),
                confirm: () => {
                    this.state.start_time = null;
                    this.state.end_time = null;
                },
            });
        }
        // Check start and end time not same
        if ((this.state.start_time && this.state.end_time) && (this.state.start_time === this.state.end_time)) {
            this.dialog.add(AlertDialog, {
                title: _t("Error"),
                body: _t("Start time and end time can't be same."),
                confirm: () => {
                    this.state.start_time = null;
                    this.state.end_time = null;
                },
            });
        }
    }
    // To check selected lead time is valid
    async onChangeLeadTime(ev) {
        if (this.state.lead_time) {
            const [hours, minutes] = this.state.lead_time.split(':').map(Number);
            const leadTimeFloat = hours + minutes / 60.0;
            const maxLeadTime = this.pos.config.reservation_lead_time;
            if (leadTimeFloat > maxLeadTime) {
                const maxHours = Math.floor(maxLeadTime);
                const maxMinutes = Math.round((maxLeadTime - maxHours) * 60);
                const maxTimeStr = `${String(maxHours).padStart(2, '0')}:${String(maxMinutes).padStart(2, '0')}`;
                this.dialog.add(AlertDialog, {
                    title: _t("Invalid Lead Time"),
                    body: _t(`The maximum lead time is set as ${maxTimeStr} hr.`),
                    confirm: () => {
                        this.state.lead_time = null;
                    },
                });
            }
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
            this.dialog.add(AlertDialog, {
                title: _t("Alert"),
                body: _t("Please fill all the required details."),
            });
        }
    }
    // Create new reservation and make payments if reservation charge enabled
    async createReservationPayment(ev) {
        this.onChangeTime()
        if (this.state.start_time > this.state.end_time){
            this.dialog.add(AlertDialog, {
                title: _t("Error"),
                body: _t("Start time can't be greater than end time."),
            });
        }
        if ((this.state.start_time && this.state.end_time) && (this.state.start_time === this.state.end_time)) {
            this.dialog.add(AlertDialog, {
                title: _t("Error"),
                body: _t("Start time and end time can't be same."),
            });
        }
        if (this.state.partner && this.state.partner != 'Select Customer') {
            if (this.state.date && this.state.start_time && this.state.end_time
                && this.state.floor && this.state.Table) {
                var order_name = this.pos.get_order() ? this.pos.get_order().name : '';
                var data = await this.orm.call('table.reservation', 'create_table_reservation', [
                        this.state.Table, this.state.date, this.state.start_time, this.state.end_time,
                        this.state.partner, this.state.lead_time, this.state.floor, order_name])
                this.props.close();
                this.pos.showScreen('ProductScreen');
                if (!this.pos.get_order()) {
                    this.pos.add_new_order();
                }
                var product = this.pos.models['product.product'].get(data)
                if (product){
                    product['lst_price'] = this.state.amount
                    await this.pos.addLineToCurrentOrder({ 
                        product_id: product,
                        price_unit: this.state.amount,
                        qty: 1
                    });
                    if (this.pos.get_order()) {
                        this.pos.get_order().set_partner(this.pos.models['res.partner'].get(parseInt(this.state.partner)))
                    }
                } else {
                    this.dialog.add(AlertDialog, {
                        title: _t("Product Not Found"),
                        body: _t("The reservation product could not be found in this POS session. Please ensure it is marked as 'Available in POS'."),
                    });
                }
            }
            else{
                this.dialog.add(AlertDialog, {
                    title: _t("Alert"),
                    body: _t("Please fill all the required details."),
                });
            }
        }
        else {
            this.dialog.add(AlertDialog, {
                    title: _t("Alert"),
                    body: _t("Please fill all the required details."),
            });
        }
    }
}
createBookingPopup.template = "createBookingPopup";
