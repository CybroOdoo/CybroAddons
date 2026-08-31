/* @odoo-module */
import { Component, useState, useRef } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
class AttendanceDashboard extends Component{
    setup(){
        this.action = useService('action')
        this.state = useState({
                        filteredDurationDates : [],
                        employeeData : []
                    })
        this.orm = useService("orm");
        this.root = useRef('attendance-dashboard')
    }
    /**
     * Event handler for the 'change' event of the filter input element.
     * It triggers the onclick_this_filter method with the new filter value.
     * @param {Event} ev - The change event object.
     */
    onChangeFilter(ev){
        ev.stopPropagation();
                this.onclick_this_filter(ev.target.value);
    }
     //on clicking search button, employees will be filtered
        _OnClickSearchEmployee(ev){
            let searchbar = this.root.el.querySelector('#search-bar').value?.toLowerCase()
            var attendance_table_rows = this.root.el.querySelector('#attendance_table_nm').children[1]
            for (let tableData of attendance_table_rows.children){
                tableData.style.display = (!tableData.children[0].getAttribute("data-name").toLowerCase().includes(searchbar)) ? 'none':'';
            }
        }
        //on clicking Print PDF button, report will be printed
        _OnClickPdfReport(ev){
        const table = this.root.el.querySelector('#attendance_table_nm')
        let tHead = table.children[0].innerHTML
        let tBody = table.children[1].innerHTML
        return this.action.doAction({
            type: 'ir.actions.report',
            report_type: 'qweb-pdf',
            report_name: 'advance_hr_attendance_dashboard.report_hr_attendance',
            report_file: 'advance_hr_attendance_dashboard.report_hr_attendance',
            data: {'tHead':tHead, 'tBody': tBody}
});
        }
    async onclick_this_filter(ev) {
            await this.orm.call(
            "hr.employee",
            "get_employee_leave_data",
            [ev]
        ).then((result) =>{
                    this.result = result
                    this.state.filteredDurationDates = result.filtered_duration_dates
                    this.state.employeeData = result.employee_data
                });
            }
    formatDate(inputDate) {
        const months = [
            'JAN', 'FEB', 'MAR', 'APR', 'MAY', 'JUN',
            'JUL', 'AUG', 'SEP', 'OCT', 'NOV', 'DEC' ];
        const parts = inputDate.split('-');
        const day = parts[2];
        const month = months[parseInt(parts[1], 10) - 1];
        const year = parts[0];
    return `${day}-${month}-${year}`;
}
}
AttendanceDashboard.template = 'AttendanceDashboard';
registry.category("actions").add("attendance_dashboard", AttendanceDashboard);
