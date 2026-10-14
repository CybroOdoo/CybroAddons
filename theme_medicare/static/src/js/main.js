import { Interaction } from "@web/public/interaction";
import { registry } from "@web/core/registry";

export class MedicareAppointment extends Interaction {
    static selector = ".appt-page-card";

    dynamicContent = {
        'select[name="department_id"]': {
            "t-on-change": this.onDepartmentChange,
        },
    };

    setup() {
        this.doctorSelect = this.el.querySelector('select[name="doctor_id"]');
        if (this.doctorSelect) {
            this.doctorOptions = Array.from(this.doctorSelect.options);
            const deptSelect = this.el.querySelector('select[name="department_id"]');
            if (deptSelect && deptSelect.value) {
                this.filterDoctors(deptSelect.value);
            }
        }
    }

    onDepartmentChange(ev) {
        this.filterDoctors(ev.currentTarget.value);
    }

    filterDoctors(selectedDepartment) {
        if (!this.doctorSelect) {
            return;
        }
        const currentDoctor = this.doctorSelect.value;
        this.doctorSelect.innerHTML = "";
        let validDoctorFound = false;

        for (const option of this.doctorOptions) {
            if (!option.value) {
                this.doctorSelect.appendChild(option);
            } else {
                const docDepartment = option.dataset.departmentId || option.getAttribute("data-department-id");
                if (!selectedDepartment || docDepartment === selectedDepartment) {
                    this.doctorSelect.appendChild(option);
                    if (option.value === currentDoctor) {
                        validDoctorFound = true;
                    }
                }
            }
        }

        this.doctorSelect.value = validDoctorFound ? currentDoctor : "";
    }
}

registry.category("public.interactions").add("theme_medicare.appointment", MedicareAppointment);
