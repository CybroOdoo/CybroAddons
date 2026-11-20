/** @odoo-module */
import { registry } from '@web/core/registry';
import { useService } from "@web/core/utils/hooks";
import { Component, onMounted, proxy } from "@odoo/owl";
import { _t } from "@web/core/l10n/translation";

class ReceptionDashBoard extends Component {
    setup() {
        super.setup();
        this.action = useService('action');
        this.orm = useService("orm");
        this.state = proxy({
            patient_lst: [],
            dr_lst: [],
            patient_id_lst: [],
            attending_dr_lst: [],
            ward_data: [],
            room_data: [],
        });
        onMounted(async () => {
            await this.createPatient();
        });
    }

    // Method for creating patient
    createPatient() {
        document.querySelectorAll('.r_active').forEach(el => {
            el.classList.remove('r_active');
        });
        document.querySelector('.o_patient_button')?.classList.add('r_active');
        document.querySelector('.room-ward')?.classList.add("d-none");
        document.querySelector('.r_Profile')?.classList.remove("d-none");
        document.querySelector('.out-patient')?.classList.add("d-none");
        document.querySelector('.inpatient')?.classList.add("d-none");
        document.querySelector('.rd_buttons')?.classList.add("d-none");
        document.querySelector('.ward')?.classList.add("d-none");
        document.querySelector('.room')?.classList.add("d-none");
    }

    // Method for save patient
    async savePatient() {
        const data = await this.fetch_patient_data();
        if (!data['name'] || !data['phone']) {
            alert("Please fill the name and phone");
            return;
        }
        await this.orm.call('res.partner', 'create', [[data]]).then(function () {
            alert("the patient record has been created");
            window.location.reload();
        });
    }

    // Method which returns the details of a patient given in the form
    fetch_patient_data() {
        const patient_name = document.querySelector('#patient-name')?.value || '';
        const patient_img = document.querySelector('#patient-img')?.dataset?.file || '';
        const patient_phone = document.querySelector('#patient-phone')?.value || '';
        const patient_mail = document.querySelector('#patient-mail')?.value || '';
        const patient_dob = document.querySelector('#patient-dob')?.value || '';
        const patient_bloodgroup = document.querySelector('#patient-bloodgroup')?.value || '';
        const patient_m_status = document.querySelector('#patient-m-status')?.value || '';
        const patient_rhtype = document.querySelector("input[name='rhtype']:checked")?.value;
        const patient_gender = document.querySelector("input[name='gender']:checked")?.value;
        const data = {
            'name': patient_name,
            'blood_group': patient_bloodgroup,
            'rh_type': patient_rhtype,
            'gender': patient_gender,
            'marital_status': patient_m_status,
            'phone': patient_phone,
            'email': patient_mail,
            'image_1920': patient_img
        };
        if (patient_dob) {
            data['date_of_birth'] = patient_dob;
        }
        return data;
    }

    // Method on clicking appointment button
    fetchAppointmentData() {
        document.querySelectorAll('.r_active').forEach(el => {
            el.classList.remove('r_active');
        });
        document.querySelector('.o_appointment_button')?.classList.add('r_active');
        document.querySelector('.room-ward')?.classList.add("d-none");
        document.querySelector('.r_Profile')?.classList.add("d-none");
        document.querySelector('.out-patient')?.classList.remove("d-none");
        document.querySelector('.inpatient')?.classList.add("d-none");
        document.querySelector('.rd_buttons')?.classList.remove("d-none");
        document.querySelector('.ward')?.classList.add("d-none");
        document.querySelector('.room')?.classList.add("d-none");
        this.createOutPatient();
    }

    // Creates new outpatient
    async createOutPatient() {
        const self = this;
        const date = new Date();
        const formattedCurrentDate = date.toISOString().split('T')[0];
        const result = await this.orm.call('res.partner', 'fetch_patient_data', []);
        this.state.patient_lst = result;
        self.patient_lst = result;
        const doctorResult = await this.orm.call('doctor.allocation', 'search_read', []);
        this.state.dr_lst = doctorResult;
        const controlsEl = document.querySelector('#controls');
        if (controlsEl) controlsEl.innerHTML = ``;
        const currentDate = new Date();
        const opDateEl = document.querySelector('#op_date');
        if (opDateEl) opDateEl.value = currentDate.toISOString().split('T')[0];
    }

    // Method for creating inpatient
    async createInPatient() {
        const self = this;
        document.querySelector('.room-ward')?.classList.add("d-none");
        document.querySelector('.r_Profile')?.classList.add("d-none");
        document.querySelector('.out-patient')?.classList.add("d-none");
        document.querySelector('.inpatient')?.classList.remove("d-none");
        document.querySelector('.ward')?.classList.add("d-none");
        document.querySelector('.room')?.classList.add("d-none");
        const domain = [['job_id.name', '=', 'Doctor']];
        const patientResult = await this.orm.call('res.partner', 'fetch_patient_data', []);
        self.patient_id_lst = patientResult;
        this.state.patient_id_lst = patientResult;
        const attendingResult = await this.orm.call('hr.employee', 'fetch_doctors_for_reception', [domain]);
        this.state.attending_dr_lst = attendingResult;
    }

    // Method for saving outpatient
    async save_out_patient_data() {
        const self = this;
        const data = await self.fetch_out_patient_data();
        if (data !== false) {
            const result = await this.orm.call('res.partner', 'create_patient', [data]);
            alert('The outpatient is created');
            const nameEl = document.querySelector('#o_patient-name');
            if (nameEl) nameEl.value = '';
            const slEl = document.querySelector('#sl_patient');
            if (slEl) slEl.value = '';
            const phoneEl = document.querySelector('#o_patient-phone');
            if (phoneEl) phoneEl.value = '';
            const dobEl = document.querySelector('#o_patient-dob');
            if (dobEl) dobEl.value = '';
        }
    }

    // Method for displaying patient card
    patient_card() {
        const selectType = document.querySelector('#select_type')?.value;
        const patientSelect = document.querySelector('#sl_patient');
        const patientLabel = document.querySelector('#patient_label');
        if (patientSelect && patientLabel) {
            if (selectType === 'dont_have_card') {
                patientSelect.style.display = 'none';
                patientLabel.style.display = 'none';
            } else {
                patientSelect.style.display = 'block';
                patientLabel.style.display = 'block';
            }
        }
    }

    // Method for fetching OP details
    async fetch_op_details() {
        const patient_id = document.querySelector('#sl_patient')?.value || '';
        const phone = document.querySelector('#o_patient-phone')?.value || '';
        const data = {
            'patient_data': patient_id,
            'patient-phone': phone
        };
        return data;
    }

    // Method for fetching patient details
    async fetch_patient_id() {
        const data = await this.fetch_op_details();
        await this.orm.call('res.partner', 'reception_op_barcode', [data]
        ).then(function (result) {
            const nameEl = document.querySelector('#o_patient-name');
            if (nameEl) nameEl.value = result.name || '';
            const dobEl = document.querySelector('#o_patient-dob');
            if (dobEl) dobEl.value = result.date_of_birth || '';
            const bloodEl = document.querySelector('#o_patient_bloodgroup');
            if (bloodEl) bloodEl.value = result.blood_group || '';
            const genderEl = document.querySelector('#o_patient-gender');
            if (genderEl) genderEl.value = result.gender || '';
            if (result.phone) {
                const phoneEl = document.querySelector('#o_patient-phone');
                if (phoneEl) phoneEl.value = result.phone;
            }
        });
    }

    // Method for fetching outpatient data
    async fetch_out_patient_data() {
        const o_patient_name = document.querySelector('#o_patient-name')?.value || '';
        const o_patient_phone = document.querySelector('#o_patient-phone')?.value || '';
        const o_patient_dob = document.querySelector('#o_patient-dob')?.value || '';
        const o_patient_blood_group = document.querySelector("#o_patient_bloodgroup")?.value || '';
        const o_patient_rhtype = document.querySelector("input[id='o_rhtype']:checked")?.value;
        const o_patient_gender = document.querySelector("input[id='o_patient-gender']:checked")?.value;
        const patient_id = document.querySelector('#sl_patient')?.value || '';
        const op_date = document.querySelector('#op_date')?.value || '';
        const reason = document.querySelector('#reason')?.value || '';
        const ticket_no = document.querySelector('#slot')?.value || '';
        const doctor = document.querySelector('#sl_dr')?.value || '';
        if (o_patient_name === '' || doctor === '' || op_date === '') {
            alert('Please fill out all the required fields.');
            return false;
        } else {
            const data = {
                'op_name': o_patient_name,
                'op_phone': o_patient_phone,
                'op_blood_group': o_patient_blood_group,
                'op_rh': o_patient_rhtype,
                'op_gender': o_patient_gender,
                'patient_id': patient_id,
                'date': op_date,
                'reason': reason,
                'slot': 0.00,
                'doctor': doctor,
            };
            if (o_patient_dob) {
                data['op_dob'] = o_patient_dob;
            }
            return data;
        }
    }

    // Method for fetching inpatient data
    async fetch_in_patient_data() {
        const patient_id = document.querySelector('#sl_patient_id')?.value;
        const reason_of_admission = document.querySelector('#reason_of_admission')?.value || '';
        const admission_type = document.querySelector('#admission_type')?.value || '';
        const attending_doctor_id = document.querySelector('#attending_doctor_id')?.value;
        if (!patient_id || !attending_doctor_id || !admission_type) {
            alert('Please fill out all the required fields.');
            return false;
        } else {
            const data = {
                'patient_id': patient_id,
                'reason_of_admission': reason_of_admission,
                'admission_type': admission_type,
                'attending_doctor_id': attending_doctor_id,
            };
            return data;
        }
    }

    // Method for creating new inpatient
    async save_in_patient_data() {
        const data = await this.fetch_in_patient_data();
        if (data != false && data != null && data != undefined) {
            this.orm.call('hospital.inpatient', 'create_new_in_patient', [null, data]
            ).then(function () {
                alert('Inpatient is created');
                const slPatientEl = document.querySelector('#sl_patient_id');
                if (slPatientEl) slPatientEl.value = '';
                const reasonEl = document.querySelector('#reason_of_admission');
                if (reasonEl) reasonEl.value = '';
                const admTypeEl = document.querySelector('#admission_type');
                if (admTypeEl) admTypeEl.value = '';
                const docEl = document.querySelector('#attending_doctor_id');
                if (docEl) docEl.value = '';
            });
        }
    }

    // Method for getting room or ward details
    fetchRoomWard() {
        const viewSecondary = document.querySelector('#view_secondary');
        if (viewSecondary) {
            viewSecondary.innerHTML = '';
        }
        document.querySelector('.room-ward')?.classList.remove("d-none");
        document.querySelector('.r_Profile')?.classList.add("d-none");
        document.querySelector('.out-patient')?.classList.add("d-none");
        document.querySelector('.inpatient')?.classList.add("d-none");
        document.querySelector('.rd_buttons')?.classList.add("d-none");
        document.querySelectorAll('.r_active').forEach(el => {
            el.classList.remove('r_active');
        });
        document.querySelector('.o_room_ward_button')?.classList.add('r_active');
    }

    // Method for getting ward details
    async fetchWard() {
        document.querySelector('.ward')?.classList.remove("d-none");
        document.querySelector('.room')?.classList.add("d-none");
        document.querySelectorAll('.r_active2').forEach(el => {
            el.classList.remove('r_active2');
        });
        document.querySelector('.o_ward_button')?.classList.add('r_active2');
        const result = await this.orm.call('hospital.ward', 'fetch_ward_details', []);
        this.state.ward_data = result;
    }

    // Method for getting room details
    async fetchRoom() {
        document.querySelector('.room')?.classList.remove("d-none");
        document.querySelector('.ward')?.classList.add("d-none");
        document.querySelectorAll('.r_active2').forEach(el => {
            el.classList.remove('r_active2');
        });
        document.querySelector('.o_room_button')?.classList.add('r_active2');
        const result = await this.orm.call('patient.room', 'fetch_rooms_details', []);
        this.state.room_data = result;
    }
}

ReceptionDashBoard.template = "ReceptionDashboard";
registry.category('actions').add('reception_dashboard_tags', ReceptionDashBoard);
