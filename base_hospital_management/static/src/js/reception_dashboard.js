/** @odoo-module */
import { registry} from '@web/core/registry';
import { useService } from "@web/core/utils/hooks";
import { Component, onMounted, useState, useRef } from "@odoo/owl";
import { _t } from "@web/core/l10n/translation";

class ReceptionDashBoard extends Component{
    setup() {
        this.ref = useRef('root');
        this.patient_creation = useRef('patient_creation');
        this.inpatient = useRef('inpatient');
        this.out_patient = useRef('out-patient');
        this.rd_buttons = useRef('rd_buttons');
        this.room_ward = useRef('room_ward');
        this.ward = useRef('ward');
        this.room = useRef('room');
        this.action = useService('action');
        this.orm = useService("orm");
        this.state = useState({
            patient_lst : [],
            ward_data : [],
            room_data : [],
            dr_lst: [],
            currentDate: new Date().toISOString().split('T')[0],
            });
        onMounted(async () => {
                await this.createPatient();
        });
    }
//  Method for creating patient
    createPatient(){
        const activeElement = this.ref.el.querySelector('.r_active');
        if (activeElement) {
            activeElement.classList.remove('r_active');
        }
        // Add active class to patient button
        const patientButton = this.ref.el.querySelector('.o_patient_button');
        if (patientButton) {
            patientButton.classList.add('r_active');
        }
//        if ($('.r_active')[0]){$('.r_active')[0].classList.remove('r_active');}
//        $('.o_patient_button')[0].classList.add('r_active');
        this.room_ward.el.classList.add("d-none")
        this.patient_creation.el.classList.remove("d-none");
        this.out_patient.el.classList.add("d-none");
        this.inpatient.el.classList.add("d-none");
        this.rd_buttons.el.classList.add("d-none");
        this.ward.el.classList.add("d-none");
        this.room.el.classList.add("d-none");
    }
//  Method for creating patient
    async savePatient (){
        var data = await this.fetch_patient_data()
        if( data['name']=="" || data['phone']==""){
            alert("Please fill the name and phone")
            return;
        }
        await this.orm.call('res.partner','create',[[data]]).then(function (){
           alert("the patient record has been created")
           window.location.reload()
        })
    }
    fetch_patient_data() {
        // Get form elements using refs or querySelector
        const getElementValue = (id) => this.ref.el.querySelector(`#${id}`)?.value || '';
        const getElementData = (id, dataAttr) =>
            this.ref.el.querySelector(`#${id}`)?.dataset[dataAttr] || '';
        const getCheckedValue = (name) =>
            this.ref.el.querySelector(`input[name='${name}']:checked`)?.value || '';
        // Fetch all form values
        const data = {
            name: getElementValue('patient-name'),
            blood_group: getElementValue('patient-bloodgroup'),
            rh_type: getCheckedValue('rhtype'),
            gender: getCheckedValue('gender'),
            marital_status: getElementValue('patient-m-status'),
            phone: getElementValue('patient-phone'),
            email: getElementValue('patient-mail'),
            image_1920: getElementData('patient-img', 'file')
        };
        // Add date of birth if it exists
        const dob = getElementValue('patient-dob');
        if (dob) {
            data.date_of_birth = dob;
        }

        return data;
    }
//  Method on clicking  appointment button
    fetchAppointmentData (){
//        if ($('.r_active')[0]){$('.r_active')[0].classList.remove('r_active');}
//        $('.o_appointment_button')[0].classList.add('r_active');
        const activeElement = this.ref.el.querySelector('.r_active');
        if (activeElement) {
            activeElement.classList.remove('r_active');
        }
        const appointmentButton = this.ref.el.querySelector('.o_appointment_button');
        if (appointmentButton) {
            appointmentButton.classList.add('r_active');
        }
        this.room_ward.el.classList.add("d-none")
        this.patient_creation.el.classList.add("d-none");
        this.out_patient.el.classList.remove("d-none");
        this.inpatient.el.classList.add("d-none");
        this.rd_buttons.el.classList.remove("d-none");
        this.ward.el.classList.add("d-none");
        this.room.el.classList.add("d-none");
        this.createOutPatient();//the outpatient creation page will be shown by default
    }
//  Creates new outpatient
    async createOutPatient (){
        var self = this;
        const date = new Date();
        var formattedCurrentDate = date.toISOString().split('T')[0];
        const result = await this.orm.call('res.partner','fetch_patient_data',[],)
        this.state.patient_lst = result;
        this.patient_lst=result
        const selectPatient = this.ref.el.querySelector('.select_patient');
//        self.patient_lst.forEach(element => {
//            $('.select_patient').append(`
//                 <option value=""></option>
//                <option value="${element['id']}">${element.patient_seq}-${element.name}</option>
//            `)
//        })

//        if (selectPatient) {
//            // Clear existing options
//            selectPatient.innerHTML = '<option value=""></option>';
//            // Add new options
//            console.log("result-->>", result)
//            result.forEach(element => {
//                const option = document.createElement('option');
//                option.value = element.id;
//                option.textContent = `${element.patient_seq}-${element.name}`;
//                selectPatient.appendChild(option);
//            });
//        }

//       await this.orm.call('doctor.allocation','search_read',[]
//       ).then(function (result){
//        self.dr_lst=result
//        $('.select_dr').html('')
//        self.dr_lst.forEach(element => {
//            $('.select_dr').append(`
//                <option value="${element['id']}">${element.display_name}</option>
//            `)
//        })
//           }),
            const doctorResult = await this.orm.call('doctor.allocation', 'search_read', []);
            this.state.dr_lst = doctorResult;
            const selectDoctor = this.ref.el.querySelector('.select_dr');
            // Update doctor dropdown
            if (selectDoctor) {
                // Clear existing options
                selectDoctor.innerHTML = '';

                // Add new options
                doctorResult.forEach(element => {
                    const option = document.createElement('option');
                    option.value = element.id;
                    option.textContent = element.display_name;
                    selectDoctor.appendChild(option);
                });
            }
            const controls = this.ref.el.querySelector('#controls');
            // Clear controls
            if (controls) {
                controls.innerHTML = '';
            }
            const opDate = this.ref.el.querySelector('#op_date');
            // Set current date
            if (opDate) {
                opDate.value = new Date().toISOString().split('T')[0];
            }

//           $('#controls').html(``);
//            var currentDate = new Date();
//            $('#op_date').val(currentDate.toISOString().split('T')[0])
    }
//  Method for creating inpatient
    async createInPatient (){
        var self = this
        this.room_ward.el.classList.add("d-none")
        this.patient_creation.el.classList.add("d-none");
        this.out_patient.el.classList.add("d-none");
        this.inpatient.el.classList.remove("d-none");
        this.ward.el.classList.add("d-none");
        this.room.el.classList.add("d-none");
        var domain = [['job_id.name', '=', 'Doctor']];
        await this.orm.call('res.partner','fetch_patient_data',[]).then(function (result){
        self.patient_id_lst=result
        const patientSelect = document.querySelector('.select_patient_id');
        patientSelect.innerHTML = ''; // Clear existing options

            self.patient_id_lst.forEach(element => {
                const option = document.createElement('option');
                option.value = element.id;
                option.textContent = `${element.patient_seq}-${element.name}`;
                patientSelect.appendChild(option);
            })
        }),
        await this.orm.call('hr.employee','search_read',[domain],)
        .then(function (result){
            self.attending_dr_lst=result
            const doctorSelect = document.querySelector('.attending_doctor_id');
            doctorSelect.innerHTML = ''; // Clear existing options
            self.attending_dr_lst.forEach(element => {
                const option = document.createElement('option');
                option.value = element.id;
                option.textContent = element.display_name;
                doctorSelect.appendChild(option);
            })
        })
    }
//  Method for saving outpatient
    async save_out_patient_data (){
        var self = this;
        var data = await self.fetch_out_patient_data ()
        if (data != false){
            var result = await this.orm.call('res.partner','create_patient',[data])
                alert('the outpatient is created');
//                $('#o_patient-name').val("");
//                $('#sl_patient').val("");
//                $('#o_patient-phone').val("");
//                $('#o_patient-dob').val("");
            // Clear the input fields using vanilla JavaScript
            document.getElementById('o_patient-name').value = "";
            document.getElementById('sl_patient').value = "";
            document.getElementById('o_patient-phone').value = "";
            document.getElementById('o_patient-dob').value = "";

        }
   }
//  Method for displaying patient card
    patient_card () {
        const selectType = document.getElementById('select_type');
        const slPatient = document.getElementById('sl_patient');
        const patientLabel = document.getElementById('patient_label');
        if (selectType.value === 'dont_have_card') {
            slPatient.style.display = 'none';
            patientLabel.style.display = 'none';
        } else {
            slPatient.style.display = 'block';
            patientLabel.style.display = 'block';
        }
//        if($('#select_type').val() === 'dont_have_card'){
//            $('#sl_patient').hide();
//            $('#patient_label').hide();
//        }
//        else{
//            $('#sl_patient').show();
//            $('#patient_label').show();
//        }
    }
//  Method for fetching OP details
    async fetch_op_details () {
//        var patient_id=$('#sl_patient').val()
//        var phone=$('#o_patient-phone').val()
        const patientId = document.getElementById('sl_patient').value;
        const phone = document.getElementById('o_patient-phone').value;
        var data={
            'patient_data':patientId        ,
            'patient-phone':phone
                  }
        return data
    }
//  Method for fetching patient details
    async fetch_patient_id () {
        var data = await this.fetch_op_details()
        await this.orm.call('res.partner', 'reception_op_barcode',[data]
        ).then(function (result) {
//            $('#o_patient-name').val(result.name)
//            $('#o_patient-dob').val(result.date_of_birth)
//            $('#o_patient_bloodgroup').val(result.blood_group)
//            $('#o_patient-gender').val(result.gender)
               document.getElementById('o_patient-name').value = result.name || '';
                document.getElementById('o_patient-dob').value = result.date_of_birth || '';
                document.getElementById('o_patient_bloodgroup').value = result.blood_group || '';
                document.getElementById('o_patient-gender').value = result.gender || '';
            if (result.phone){
                document.getElementById('o_patient-phone').value = result.phone;
//                $('#o_patient-phone').val(result.phone)
            }
        });
    }
//  Method for fetching outpatient data
    async fetch_out_patient_data () {
//        var o_patient_name = $('#o_patient-name').val();
//        var o_patient_phone = $('#o_patient-phone').val();
//        var o_patient_dob = $('#o_patient-dob').val();
//        var o_patient_blood_group = $("#o_patient_bloodgroup").val();
//        var o_patient_rhtype = $("input[id='o_rhtype']:checked").val();
//        var o_patient_gender = $("input[id='o_patient-gender']:checked").val();
//        var patient_id = $('#sl_patient').val();
//        var op_date = $('#op_date').val();
//        var reason = $('#reason').val();
//        var ticket_no = $('#slot').val();
//        var doctor = $('#sl_dr').val();
        const oPatientName = document.getElementById('o_patient-name').value;
        const oPatientPhone = document.getElementById('o_patient-phone').value;
        const oPatientDob = document.getElementById('o_patient-dob').value;
        const oPatientBloodGroup = document.getElementById('o_patient_bloodgroup').value;
        const oPatientRhType = document.querySelector("input[id='o_rhtype']:checked")?.value || null;
        const oPatientGender = document.querySelector("input[id='o_patient-gender']:checked")?.value || null;
        const patientId = document.getElementById('sl_patient').value;
        const opDate = document.getElementById('op_date').value;
        const reason = document.getElementById('reason').value;
        const ticketNo = document.getElementById('slot').value;
        const doctor = document.getElementById('sl_dr').value;
//        if (o_patient_name === '' || doctor === '' || op_date === '') {
//            alert('Please fill out all the required fields.');
//            return false; // Prevent form submission
//        }
        if (!oPatientName || !doctor || !opDate) {
        alert('Please fill out all the required fields.');
        return false; // Prevent further execution
    }

        else{
//            var data = {
//                'op_name':o_patient_name,
//                'op_phone':o_patient_phone,
//                'op_blood_group':o_patient_blood_group,
//                'op_rh':o_patient_rhtype,
//                'op_gender':o_patient_gender,
//                'patient_id' : patient_id,
//                'date' : op_date,
//                'reason' : reason,
//                'slot' : 0.00,
//                'doctor' : doctor,
//            }
            const data = {
                    op_name: oPatientName,
                    op_phone: oPatientPhone,
                    op_blood_group: oPatientBloodGroup,
                    op_rh: oPatientRhType,
                    op_gender: oPatientGender,
                    patient_id: patientId,
                    date: opDate,
                    reason: reason,
                    slot: 0.00,
                    doctor: doctor,
                };
            if (o_patient_dob) {
//                data['op_dob'] = o_patient_dob;
                data.op_dob = oPatientDob;
            }
            return data
        }
    }
//  Method for fetching inpatient data
    async fetch_in_patient_data (){
//        var patient_id = $('#sl_patient_id').val();
//        var reason_of_admission = $('#reason_of_admission').val();
//        var admission_type = $('#admission_type').val();
//        var attending_doctor_id = $('#attending_doctor_id').val();
        const patientId = document.getElementById('sl_patient_id').value;
        const reasonOfAdmission = document.getElementById('reason_of_admission').value;
        const admissionType = document.getElementById('admission_type').value;
        const attendingDoctorId = document.getElementById('attending_doctor_id').value;
//        if (patient_id === null || attending_doctor_id === null ||
//        admission_type === null) {
//            alert('Please fill out all the required fields.');
//            return false; // Prevent form submission
//        }
        if (!patientId || !attendingDoctorId || !admissionType) {
            alert('Please fill out all the required fields.');
            return false; // Prevent further execution
        }
        else{
//            var data = {
//                'patient_id' : patient_id,
//                'reason_of_admission' : reason_of_admission,
//                'admission_type' : admission_type,
//                'attending_doctor_id' : attending_doctor_id,
//            }
                const data = {
                        patient_id: patientId,
                        reason_of_admission: reasonOfAdmission,
                        admission_type: admissionType,
                        attending_doctor_id: attendingDoctorId,
                    };
            return data
        }
    }
//  Method for creating new inpatient
    async save_in_patient_data (){
//        var data = await this.fetch_in_patient_data()
        const data = await this.fetch_in_patient_data();
        if (data != false || data != null || data != undefined){
            this.orm.call('hospital.inpatient','create_new_in_patient',[null,data]
            ).then(function (){
                alert('Inpatient is created');
                    document.getElementById('sl_patient_id').value = "";
                    document.getElementById('reason_of_admission').value = "";
                    document.getElementById('admission_type').value = "";
                    document.getElementById('attending_doctor_id').value = "";
//                  $('#sl_patient_id').val("");
//                  $('#reason_of_admission').val("");
//                  $('#admission_type').val("");
//                  $('#attending_doctor_id').val("");
        });
        }
    }
//  Method for getting room or ward details
    fetchRoomWard (){
//        $('#view_secondary').html('');
        const viewSecondary = document.getElementById('view_secondary');
        if (viewSecondary) {
            viewSecondary.innerHTML = '';
        }
        this.room_ward.el.classList.remove("d-none")
        this.patient_creation.el.classList.add("d-none");
        this.out_patient.el.classList.add("d-none");
        this.inpatient.el.classList.add("d-none");
        this.rd_buttons.el.classList.add("d-none");
//        if ($('.r_active')[0]){$('.r_active')[0].classList.remove('r_active');}
//        $('.o_room_ward_button')[0].classList.add('r_active');
        const activeElement = document.querySelector('.r_active');
        if (activeElement) {
            activeElement.classList.remove('r_active');
        }
        const roomWardButton = document.querySelector('.o_room_ward_button');
        if (roomWardButton) {
            roomWardButton.classList.add('r_active');
        }
    }
//  Method for getting ward details
    async fetchWard (){
        this.ward.el.classList.remove("d-none");
        this.room.el.classList.add("d-none");
//        if ($('.r_active2')[0]){$('.r_active2')[0].classList.remove('r_active2');}
//        $('.o_ward_button')[0].classList.add('r_active2');
        const activeElement = document.querySelector('.r_active2');
            if (activeElement) {
                activeElement.classList.remove('r_active2');
            }
        const wardButton = document.querySelector('.o_ward_button');
            if (wardButton) {
                wardButton.classList.add('r_active2');
            }
        var result = await this.orm.call('hospital.ward','search_read',)
        this.state.ward_data = result
    }
//  Method for getting room details
    async fetchRoom (){
        this.room.el.classList.remove("d-none");
        this.ward.el.classList.add("d-none");
//        if ($('.r_active2')[0]){$('.r_active2')[0].classList.remove('r_active2');}
//        $('.o_room_button')[0].classList.add('r_active2');
        const activeElement = document.querySelector('.r_active2');
        if (activeElement) {
            activeElement.classList.remove('r_active2');
        }
        // Add the "r_active2" class to the room button
        const roomButton = document.querySelector('.o_room_button');
        if (roomButton) {
            roomButton.classList.add('r_active2');
        }
        var result= await this.orm.call('patient.room','search_read',)
        this.state.room_data = result
    }
}
ReceptionDashBoard.template = "ReceptionDashboard"
registry.category('actions').add('reception_dashboard_tags', ReceptionDashBoard);
