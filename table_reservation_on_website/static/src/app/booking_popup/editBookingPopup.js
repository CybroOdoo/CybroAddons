/**@odoo-module **/
import { AlertDialog } from "@web/core/confirmation_dialog/confirmation_dialog";
import { usePos } from "@point_of_sale/app/store/pos_hook";
import { Component, useState } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";
import { _t } from "@web/core/l10n/translation";
import { Dialog } from "@web/core/dialog/dialog";

export class EditBookingPopup extends Component {
    static components = { Dialog };
    static props = {
        close: Function,
        title: String,
        data: { type: Object, optional: true },
        getPayload: { type: Function, optional: true },
    };
    async setup() {
        super.setup();
        this.orm = useService('orm')
        this.dialog = useService("dialog")
        this.pos = usePos()
        const floors = this.pos.models["restaurant.floor"].getAll()
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
            Partners: this.pos.models["res.partner"].getAll(),
            floors: this.pos.models["restaurant.floor"].getAll(),
            tables: [],
            time:'',
            table_details_header: false,
        });
        if ((this.state.StartingTime && this.state.EndTime) && (this.state.StartingTime === this.state.EndTime)){
            this.dialog.add(AlertDialog, {
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
                this.dialog.add(AlertDialog, {
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
        if (!this.state.Date || isNaN(new Date(this.state.Date).getTime()) || new Date(this.state.Date).getFullYear() < 1000) {
            return;
        }
        var selectedDate = new Date(this.state.Date);
        if (selectedDate.getFullYear() > 9999) {
            this.dialog.add(AlertDialog, {
                title: _t("Invalid Date"),
                body: _t("Invalid Year."),
                confirm: () => {
                    this.state.Date = '';
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
                    this.state.Date = '';
                },
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
                 this.dialog.add(AlertDialog, {
                    title: _t("Invalid Time"),
                    body: _t("You can't select past time."),
                    confirm: () => {
                        this.state.StartingTime = null;
                    },
                 });
            }
            if (this.state.EndTime && this.state.EndTime < currentTime) {
                this.dialog.add(AlertDialog, {
                    title: _t("Invalid Time"),
                    body: _t("You can't select past time."),
                    confirm: () => {
                        this.state.EndTime = null;
                    },
                });
            }
        }
        if ((this.state.StartingTime && this.state.EndTime) && (this.state.StartingTime === this.state.EndTime)){
            this.dialog.add(AlertDialog, {
                title: _t("Error"),
                body: _t("Start time and end time can't be same."),
                confirm: () => {
                    this.state.StartingTime = null;
                    this.state.EndTime = null;
                },
            });
        }
        if ((this.state.StartingTime && this.state.EndTime) && (this.state.StartingTime > this.state.EndTime)){
            this.dialog.add(AlertDialog, {
                title: _t("Error"),
                body: _t("Start time can't be greater than end time."),
                confirm: () => {
                    this.state.StartingTime = null;
                    this.state.EndTime = null;
                },
            });
        }
    }
    // To Check selected lead time is valid
    async onChangeLeadTime(ev) {
        if (this.state.time) {
            const [hours, minutes] = this.state.time.split(':').map(Number);
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
                        this.convertDecimalToTime(this.props.data?.lead_time || 0);
                        this.state.LeadTime = this.props.data?.lead_time || 0;
                    },
                });
            } else {
                this.state.LeadTime = leadTimeFloat;
            }
        }
    }
    // Save the edited reservation details
    async saveData() {
        var partners = this.pos.models["res.partner"].getAll()
        var booking_id = this.props.data['id']
        var date = this.state.Date
        var customer = this.state.customerId
        var start_time = this.state.StartingTime
        var end_time = this.state.EndTime
        var floor = this.state.Floor
        var table_ids = this.state.Table
        var lead_time = this.state.LeadTime
        this.onChangeTime()
        var order_name = this.pos.get_order() ? this.pos.get_order().name : '';
        if (partners && booking_id && date && customer && start_time && end_time && floor && table_ids.length > 0) {
            var data = await this.orm.call('table.reservation', 'edit_reservations', [
                booking_id, date, customer, start_time, end_time, floor, table_ids, lead_time, order_name
            ]);
            var order = this.pos.models['pos.order'].find(order => order.name === this.props.data.order_name);
            if (order) {
                this.pos.removeOrder(order);
            }
            if (!this.pos.get_order()) {
                this.pos.add_new_order();
            }
            var product = this.pos.models['product.product'].get(data)
            if (product) {
                product['lst_price'] = this.state.BookingAmount
                await this.pos.addLineToCurrentOrder({
                    product_id: product,
                    price_unit: this.state.BookingAmount,
                    qty: 1
                });
                if (this.pos.get_order()) {
                    this.pos.get_order().set_partner(this.pos.models['res.partner'].get(parseInt(this.state.customerId)))
                }
            } else {
                this.dialog.add(AlertDialog, {
                    title: _t("Product Not Found"),
                    body: _t("The reservation product could not be found in this POS session. Please ensure it is marked as 'Available in POS'."),
                });
            }
            this.props.close();
            location.reload();
        }
        else {
            this.dialog.add(AlertDialog, {
                title: _t("Alert"),
                body: _t("Please fill all the required details."),
            });
        }
    }
    // Edit reservation and make payments if reservation charge enabled
    async editReservationPayment(ev) {
        this.onChangeTime()
        if (this.state.StartingTime > this.state.EndTime) {
            this.dialog.add(AlertDialog, {
                title: _t("Error"),
                body: _t("Start time can't be greater than end time."),
            });
        }
        if ((this.state.StartingTime && this.state.EndTime) && (this.state.StartingTime === this.state.EndTime)) {
            this.dialog.add(AlertDialog, {
                title: _t("Error"),
                body: _t("Start time and end time can't be same."),
            });
        }

        var partners = this.pos.models["res.partner"].getAll()
        var booking_id = this.props.data['id']
        var date = this.state.Date
        var customer = this.state.customerId
        var start_time = this.state.StartingTime
        var end_time = this.state.EndTime
        var floor = this.state.Floor
        var table_ids = this.state.Table
        var lead_time = this.state.LeadTime

        if (customer && customer != 'Select Partner') {
            if (partners && booking_id && date && start_time && end_time && floor && table_ids.length > 0) {
                var order_name = this.pos.get_order() ? this.pos.get_order().name : '';
                var data = await this.orm.call('table.reservation', 'edit_reservations', [
                    booking_id, date, customer, start_time, end_time, floor, table_ids, lead_time, order_name
                ]);

                var order = this.pos.models['pos.order'].find(order => order.name === this.props.data.order_name);
                if (order) {
                    this.pos.removeOrder(order);
                }

                this.props.close();
                this.pos.showScreen('ProductScreen');

                if (!this.pos.get_order()) {
                    this.pos.add_new_order();
                }

                var product = this.pos.models['product.product'].get(data)
                if (product) {
                    product['lst_price'] = this.state.BookingAmount
                    await this.pos.addLineToCurrentOrder({
                        product_id: product,
                        price_unit: this.state.BookingAmount,
                        qty: 1
                    });
                    if (this.pos.get_order()) {
                        this.pos.get_order().set_partner(this.pos.models['res.partner'].get(parseInt(this.state.customerId)))
                    }
                } else {
                    this.dialog.add(AlertDialog, {
                        title: _t("Product Not Found"),
                        body: _t("The reservation product could not be found in this POS session. Please ensure it is marked as 'Available in POS'."),
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
        else {
            this.dialog.add(AlertDialog, {
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
