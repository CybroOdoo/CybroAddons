import { Interaction } from "@web/public/interaction";
import { registry } from "@web/core/registry";
import { rpc } from "@web/core/network/rpc";

export class DoctorBooking extends Interaction {
    static selector = "#booking_form";
    dynamicContent = {
        "#booking_date": {
            "t-on-change": this.changeBookingDate,
        },
        "#doctor-department": {
            "t-on-change": this.updateDoctorOptions,
        },
    };

    start() {
        const doctorSelect = this.el.querySelector("#doctor-name");
        // If doctors not yet loaded, fetch them for current date
        if (doctorSelect && doctorSelect.options.length <= 1) {
            this.changeBookingDate();
        }
    }

    // Method for checking booking date
    async changeBookingDate() {
        const dateInput = this.el.querySelector("#booking_date");
        const selectedDate = dateInput ? dateInput.value : null;
        if (!selectedDate) {
            return;
        }
        const data = await this.waitFor(
            rpc("/patient_booking/get_doctors", {
                selected_date: selectedDate,
                department: false,
            })
        );
        const doctorSelect = this.el.querySelector("#doctor-name");
        const departmentSelect = this.el.querySelector("#doctor-department");

        if (doctorSelect) {
            doctorSelect.innerHTML = "";
            const defaultDocOpt = document.createElement("option");
            defaultDocOpt.value = "";
            defaultDocOpt.textContent = "Select Doctor...";
            doctorSelect.appendChild(defaultDocOpt);
            data.doctors.forEach((doctor) => {
                const option = document.createElement("option");
                option.value = doctor.id;
                option.textContent = doctor.name;
                doctorSelect.appendChild(option);
            });
        }

        if (departmentSelect) {
            const currentDept = departmentSelect.value;
            departmentSelect.innerHTML = "";
            const defaultDeptOpt = document.createElement("option");
            defaultDeptOpt.value = "";
            defaultDeptOpt.textContent = "Select Department...";
            departmentSelect.appendChild(defaultDeptOpt);
            data.departments.forEach((dep) => {
                const option = document.createElement("option");
                option.value = dep.id;
                option.textContent = dep.name;
                departmentSelect.appendChild(option);
            });
            if (currentDept && Array.from(departmentSelect.options).some((o) => o.value == currentDept)) {
                departmentSelect.value = currentDept;
                await this.updateDoctorOptions();
            }
        }
    }

    // Method for updating doctor options when department changes
    async updateDoctorOptions() {
        const dateInput = this.el.querySelector("#booking_date");
        const selectedDate = dateInput ? dateInput.value : null;
        const deptSelect = this.el.querySelector("#doctor-department");
        const department = deptSelect ? deptSelect.value : false;
        const data = await this.waitFor(
            rpc("/patient_booking/get_doctors", {
                selected_date: selectedDate,
                department: department || false,
            })
        );
        const doctorSelect = this.el.querySelector("#doctor-name");
        if (doctorSelect) {
            doctorSelect.innerHTML = "";
            const defaultDocOpt = document.createElement("option");
            defaultDocOpt.value = "";
            defaultDocOpt.textContent = "Select Doctor...";
            doctorSelect.appendChild(defaultDocOpt);
            data.doctors.forEach((doctor) => {
                const option = document.createElement("option");
                option.value = doctor.id;
                option.textContent = doctor.name;
                doctorSelect.appendChild(option);
            });
        }
    }
}

registry
    .category("public.interactions")
    .add("base_hospital_management.doctor_booking", DoctorBooking);

