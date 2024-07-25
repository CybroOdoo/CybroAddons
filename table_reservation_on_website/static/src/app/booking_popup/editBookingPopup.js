/**@odoo-module **/
import { AbstractAwaitablePopup } from "@point_of_sale/app/popup/abstract_awaitable_popup";
import { ConfirmPopup } from "@point_of_sale/app/utils/confirm_popup/confirm_popup";
import { ErrorPopup } from "@point_of_sale/app/errors/popups/error_popup";
import { usePos } from "@point_of_sale/app/store/pos_hook";
import { useService } from "@web/core/utils/hooks";
import { useState } from "@odoo/owl";
import { _t } from "@web/core/l10n/translation";

export class EditBookingPopup extends AbstractAwaitablePopup {
    async setup() {
        super.setup();
        this.orm = useService('orm')
        this.popup = useService("popup")
        this.pos = usePos()
        const floors = this.env.services.pos.floors
        const tables = floors.find(floor => floor.id === this.props.data?.floor_id[0])?.tables || [];
        const bookedTableIds = this.props.data?.booked_tables_ids || [];
        const parsedBookedTableIds = typeof bookedTableIds === 'string'
            ? bookedTableIds.split(',').map(Number).filter(id => !isNaN(id))
            : [...bookedTableIds];
        this.state = useState({
            customerId: this.props.data?.customer_id[0],
            Date: this.props.data?.date,
            StartingTime: this.props.data?.starting_at,
            EndTime: this.props.data?.ending_at,
            Floor: this.props.data?.floor_id[0],
            TableList: parsedBookedTableIds,
            Table: parsedBookedTableIds.join(','),
            BookingAmount: this.props.data?.booking_amount,
            OrderType: this.props.data?.type,
            LeadTime: this.props.data?.lead_time,
            Partners: this.env.services.pos.partners,
            floors: this.env.services.pos.floors,
            tables: [],
            time:'',
            table_details_header: false,
        });
        if ((this.state.StartingTime && this.state.EndTime) && (this.state.StartingTime === this.state.EndTime)){
            this.popup.add(ConfirmPopup, {
                title: _t("Error"),
                body: _t("Start time and end time can't be same."),
            });
        }
        this.convertDecimalToTime(this.state.LeadTime)
        var table_data = await this.orm.call('table.reservation', 'get_table_details', [
                    this.state.Floor, this.state.Date, this.state.StartingTime, this.state.EndTime, this.state.TableList])
        this.state.tables = table_data
    }
    // Convert lead time number to string
    convertDecimalToTime(decimalHours) {
        const [hours, decimalMinutes] = decimalHours.toString().split('.');
        const minutes = decimalMinutes ? decimalMinutes.padEnd(2, '0') : '00';
        const formattedHours = String(hours).padStart(2, '0');
        const formattedMinutes = String(minutes).padStart(2, '0');
        this.state.time = `${formattedHours}:${formattedMinutes}`;
    }
    // Partner details
    selectPartner(ev) {
        this.state.customerId = parseInt(ev.target.value)
    }
    // Filter tables according to selected floor
    async onSelectFloor(ev) {
        this.state.BookingAmount = ''
        this.state.TableList = [];
        if (ev.target.options[ev.target.selectedIndex].text != 'Select Floor'){
            this.state.table_details_header = true
            this.state.Floor = parseInt(ev.target.value)
            var table_data = []
            var date = this.state.Date
            var start_time = this.state.StartingTime
            var end_time = this.state.EndTime
            var floor_id = this.state.Floor
            this.state.Table = ''
            if (start_time > end_time){
                this.popup.add(ErrorPopup, {
                    title: _t("Error"),
                    body: _t("Start time can't be greater than end time."),
                });
            }
            if (floor_id && date && start_time && end_time){
                var table_data = await this.orm.call('table.reservation', 'get_table_details', [
                    floor_id, date, start_time, end_time, this.props.data.booked_tables_ids])
                this.state.tables = table_data
            }
        }
    }
    // To Check selected date is valid one
    async onChangeDate() {
        var selectedDate = new Date($("#date").val());
        const currentDate = new Date();
        if (selectedDate < currentDate.setHours(0, 0, 0, 0)){
            this.popup.add(ErrorPopup, {
                title: _t("Invalid Date"),
                body: _t("Please select a valid date."),
            }).then(() => {
                $("#date").val('')
            });
        }
        this.onChangeTime()
    }
    // To check selected start time is not past one
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
        if (this.state.Date == formattedDate){
            if (this.state.StartingTime && this.state.StartingTime < currentTime) {
                 this.popup.add(ErrorPopup, {
                    title: _t("Invalid Time"),
                    body: _t("You can't select past time."),
                 }).then(() => {
                    this.state.StartingTime = null;
                 });
            }
            if (this.state.EndTime && this.state.EndTime < currentTime) {
                this.popup.add(ErrorPopup, {
                    title: _t("Invalid Time"),
                    body: _t("You can't select past time."),
                 }).then(() => {
                    this.state.EndTime = null;
                });
            }
        }
        if ((this.state.StartingTime && this.state.EndTime) && (this.state.StartingTime === this.state.EndTime)){
            this.popup.add(ErrorPopup, {
                title: _t("Error"),
                body: _t("Start time and end time can't be same."),
            }).then(() => {
                this.state.StartingTime = null;
                this.state.EndTime = null;
            });
        }
        if ((this.state.StartingTime && this.state.EndTime) && (this.state.StartingTime > this.state.EndTime)){
            this.popup.add(ErrorPopup, {
                title: _t("Error"),
                body: _t("Start time can't be greater than end time."),
            }).then(() => {
                this.state.StartingTime = null;
                this.state.EndTime = null;
            });
        }
    }
    // To Check selected lead time is valid
    async onChangeLeadTime(ev) {
        if (isNaN(this.state.LeadTime)) {
            this.popup.add(ErrorPopup, {
                title: _t("Invalid Lead Time"),
                body: _t("Please select a valid lead time."),
            }).then(() => {
                this.state.LeadTime = null;
            });
        }
        this.state.LeadTime = ev.target.value
        this.convertDecimalToTime(this.state.LeadTime)
    }
    // Save the edited reservation details
    async saveData() {
        var partners = this.env.services.pos.partners
        var booking_id = this.props.data['id']
        var date = this.state.Date
        var customer = this.state.customerId
        var start_time = this.state.StartingTime
        var end_time = this.state.EndTime
        var floor = this.state.Floor
        var table_ids = this.state.Table
        var lead_time = this.state.LeadTime
        this.onChangeTime()
        if (partners && booking_id && date && customer && start_time && end_time && floor && table_ids.length>0){
            var data = await this.orm.call('table.reservation', 'edit_reservations', [
                booking_id, date, customer, start_time, end_time, floor, table_ids, lead_time, this.pos.get_order().name
            ]);
            var order = this.pos.orders.find(order => order.name === this.props.data.order_name);
            if (order){
                this.pos.removeOrder(order);
                var product = this.pos.db.product_by_id[data]
                if (product){
                    product['lst_price'] = this.state.BookingAmount
                }
                this.pos.get_order().set_partner(this.pos.db.partner_by_id[parseInt(this.state.customerId)])
                this.pos.get_order().add_product(product, {
                    quantity: 1,
                });
            }
            location.reload();
        }
        else {
            this.popup.add(ErrorPopup, {
                title: _t("Alert"),
                body: _t("Please fill all the required details."),
            });
        }
    }
    // Select tables for booking
    async onSelectTable(event) {
        const tableDiv = event.target.closest('.card_table');
        const tableId = parseInt(tableDiv.getAttribute('data-id'), 10);
        let currentTableList = [...this.state.TableList];
        let currentTable = this.state.Table ? this.state.Table.split(',').map(Number) : [];
        if (tableDiv.style.backgroundColor == 'green') {
            tableDiv.style.backgroundColor = '#2980b9';
            currentTableList = currentTableList.filter(id => id !== tableId);
            currentTable = currentTable.filter(id => id !== tableId);
        }
        else {
            currentTableList.push(tableId);
            currentTable.push(tableId);
            tableDiv.style.backgroundColor = 'green';
        }
        // Update state with the new values
        this.state.TableList = currentTableList;
        this.state.Table = currentTable.join(',');
        if(this.state.Floor){
            var reservation_amount = await this.orm.call('table.reservation', 'get_reservation_amount', [this.state.Table])
            this.state.BookingAmount = reservation_amount
        }
    }
}
EditBookingPopup.template = "EditBookingPopup";
