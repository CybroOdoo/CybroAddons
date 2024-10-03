/* @odoo-module */
const { Component, useState } = owl;
const { useRef } = owl.hooks;
import { registry } from "@web/core/registry";
import rpc from "web.rpc";
import { useService } from "@web/core/utils/hooks";
class AttendanceDashboard extends Component {
    setup() {
        this.action = useService('action')
        this.state = useState({
            filteredDurationDates: [],
            employeeData: []
        })
        this.root = useRef('attendance-dashboard')
        // Apply the "This Week" filter by default
        this.onclick_this_filter("this_week")
    }
    onChangeFilter(ev) {
        ev.stopPropagation();
        this.onclick_this_filter(ev.target.value);
    }
    _OnClickSearchEmployee(ev) {
        let searchbar = this.root.el.querySelector('#search-bar').value?.toLowerCase()
        var attendance_table_rows = this.root.el.querySelector('#attendance_table_nm').children[1]
        for (let tableData of attendance_table_rows.children) {
            tableData.style.display = (!tableData.children[0].getAttribute("data-name").toLowerCase().includes(searchbar)) ? 'none' : '';
        }
    }
    _OnClickPdfReport(ev) {
        const table = this.root.el.querySelector('#attendance_table_nm')
        let tHead = table.children[0].innerHTML
        let tBody = table.children[1].innerHTML
        return this.action.doAction({
            type: 'ir.actions.report',
            report_type: 'qweb-pdf',
            report_name: 'advance_hr_attendance_dashboard.report_hr_attendance',
            report_file: 'advance_hr_attendance_dashboard.report_hr_attendance',
            data: { 'tHead': tHead, 'tBody': tBody }
        });
    }
    async onclick_this_filter(filter) {
        await rpc.query({
            model: "hr.employee",
            method: "get_employee_leave_data",
            args: [filter]
        }).then((result) => {
            this.result = result
            this.state.filteredDurationDates = result.filtered_duration_dates
            this.state.employeeData = result.employee_data
        });
    }
    formatDate(inputDate) {
        const months = [
            'JAN', 'FEB', 'MAR', 'APR', 'MAY', 'JUN',
            'JUL', 'AUG', 'SEP', 'OCT', 'NOV', 'DEC'
        ];
        const parts = inputDate.split('-');
        const day = parts[2];
        const month = months[parseInt(parts[1], 10) - 1];
        const year = parts[0];
        return `${day}-${month}-${year}`;
    }
}
AttendanceDashboard.template = 'AttendanceDashboard';
registry.category("actions").add("attendance_dashboard", AttendanceDashboard);
