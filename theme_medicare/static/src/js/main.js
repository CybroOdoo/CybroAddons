/** @odoo-module **/

// Medicare Theme JS Placeholder
// is natively supported by Odoo's website architecture and qweb templates.

import publicWidget from "@web/legacy/js/public/public_widget";

publicWidget.registry.MedicareAppointment = publicWidget.Widget.extend({
    selector: '.appt-page-card',
    events: {
        'change select[name="department_id"]': '_onDepartmentChange',
    },

    start: function () {
        this.doctorSelect = this.el.querySelector('select[name="doctor_id"]');
        if (this.doctorSelect) {
            this.doctorOptions = Array.from(this.doctorSelect.options);
            // Trigger initial change if there is a selected department
            const deptSelect = this.el.querySelector('select[name="department_id"]');
            if (deptSelect && deptSelect.value) {
                this._onDepartmentChange({ currentTarget: deptSelect });
            }
        }
        return this._super.apply(this, arguments);
    },

    _onDepartmentChange: function (ev) {
        if (!this.doctorSelect) return;

        const selectedDepartment = ev.currentTarget.value;
        const currentDoctor = this.doctorSelect.value;
        this.doctorSelect.innerHTML = "";

        let validDoctorFound = false;

        this.doctorOptions.forEach(option => {
            if (!option.value) {
                this.doctorSelect.appendChild(option);
            } else {
                const docDepartment = option.dataset.departmentId || option.getAttribute('data-department-id');
                if (!selectedDepartment || docDepartment === selectedDepartment) {
                    this.doctorSelect.appendChild(option);
                    if (option.value === currentDoctor) {
                        validDoctorFound = true;
                    }
                }
            }
        });

        if (validDoctorFound) {
            this.doctorSelect.value = currentDoctor;
        } else {
            this.doctorSelect.value = "";
        }
    },
});

export default publicWidget.registry.MedicareAppointment;
