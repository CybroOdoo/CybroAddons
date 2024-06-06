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
            });
        onMounted(async () => {
                await this.createPatient();
        });
    }
//  Method for creating patient
    createPatient(){
        if ($('.r_active')[0]){$('.r_active')[0].classList.remove('r_active');}
        $('.o_patient_button')[0].classList.add('r_active');
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
//  Method which returns the details of a patient given in the form
    fetch_patient_data (){
        var patient_name = $('#patient-name').val();
        var patient_img = $('#patient-img').data('file');
        var patient_phone = $('#patient-phone').val();
        var patient_mail = $('#patient-mail').val();
        var patient_dob = $('#patient-dob').val();
        var patient_bloodgroup = $('#patient-bloodgroup').val();
        var patient_m_status = $('#patient-m-status').val() || '';
        var patient_rhtype = $("input[name='rhtype']:checked").val();
        var patient_gender = $("input[name='gender']:checked").val();
        var data = {
            'name' : patient_name,
            'blood_group' : patient_bloodgroup,
            'rh_type' : patient_rhtype,
            'gender' : patient_gender,
            'marital_status' : patient_m_status,
            'phone' : patient_phone,
            'email' : patient_mail,
            'image_1920': patient_img
        }
        if (patient_dob) {
            data['date_of_birth'] = patient_dob;
        }
        return data
    }
//  Method on clicking  appointment button
    fetchAppointmentData (){
        if ($('.r_active')[0]){$('.r_active')[0].classList.remove('r_active');}
        $('.o_appointment_button')[0].classList.add('r_active');
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
        this.state.patient_lst = result
        self.patient_lst=result
        self.patient_lst.forEach(element => {
            $('.select_patient').append(`
                 <option value=""></option>
                <option value="${element['id']}">${element.patient_seq}-${element.name}</option>
            `)
        })
       await this.orm.call('doctor.allocation','search_read',[]
       ).then(function (result){
        self.dr_lst=result
        $('.select_dr').html('')
        self.dr_lst.forEach(element => {
            $('.select_dr').append(`
                <option value="${element['id']}">${element.display_name}</option>
            `)
        })
           }),
           $('#controls').html(``);
            var currentDate = new Date();
            $('#op_date').val(currentDate.toISOString().split('T')[0])
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
        $('.select_patient_id').html('')
            self.patient_id_lst.forEach(element => {
                $('.select_patient_id').append(`
                    <option value="${element['id']}">${element.patient_seq}-${element.name}</option>
                `)
            })
        }),
        await this.orm.call('hr.employee','search_read',[domain],)
        .then(function (result){
            self.attending_dr_lst=result
            $('.attending_doctor_id').html('')
            self.attending_dr_lst.forEach(element => {
                $('.attending_doctor_id').append(`
                    <option value="${element['id']}">${element.display_name}</option>
                `)
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
                $('#o_patient-name').val("");
                $('#sl_patient').val("");
                $('#o_patient-phone').val("");
                $('#o_patient-dob').val("");

        }
   }
//  Method for displaying patient card
    patient_card () {
        if($('#select_type').val() === 'dont_have_card'){
            $('#sl_patient').hide();
            $('#patient_label').hide();
        }
        else{
            $('#sl_patient').show();
            $('#patient_label').show();
        }
    }
//  Method for fetching OP details
    async fetch_op_details () {
        var patient_id=$('#sl_patient').val()
        var phone=$('#o_patient-phone').val()
        var data={
            'patient_data':patient_id,
            'patient-phone':phone
                  }
        return data
    }
//  Method for fetching patient details
    async fetch_patient_id () {
        var data = await this.fetch_op_details()
        await this.orm.call('res.partner', 'reception_op_barcode',[data]
        ).then(function (result) {
            $('#o_patient-name').val(result.name)
            $('#o_patient-dob').val(result.date_of_birth)
            $('#o_patient_bloodgroup').val(result.blood_group)
            $('#o_patient-gender').val(result.gender)
            if (result.phone){
                $('#o_patient-phone').val(result.phone)
            }
        });
    }
//  Method for fetching outpatient data
    async fetch_out_patient_data () {
        var o_patient_name = $('#o_patient-name').val();
        var o_patient_phone = $('#o_patient-phone').val();
        var o_patient_dob = $('#o_patient-dob').val();
        var o_patient_blood_group = $("#o_patient_bloodgroup").val();
        var o_patient_rhtype = $("input[id='o_rhtype']:checked").val();
        var o_patient_gender = $("input[id='o_patient-gender']:checked").val();
        var patient_id = $('#sl_patient').val();
        var op_date = $('#op_date').val();
        var reason = $('#reason').val();
        var ticket_no = $('#slot').val();
        var doctor = $('#sl_dr').val();
        if (o_patient_name === '' || doctor === '' || op_date === '') {
            alert('Please fill out all the required fields.');
            return false; // Prevent form submission
        }
        else{
            var data = {
                'op_name':o_patient_name,
                'op_phone':o_patient_phone,
                'op_blood_group':o_patient_blood_group,
                'op_rh':o_patient_rhtype,
                'op_gender':o_patient_gender,
                'patient_id' : patient_id,
                'date' : op_date,
                'reason' : reason,
                'slot' : 0.00,
                'doctor' : doctor,
            }
            if (o_patient_dob) {
                data['op_dob'] = o_patient_dob;
            }
            return data
        }
    }
//  Method for fetching inpatient data
    async fetch_in_patient_data (){
        var patient_id = $('#sl_patient_id').val();
        var reason_of_admission = $('#reason_of_admission').val();
        var admission_type = $('#admission_type').val();
        var attending_doctor_id = $('#attending_doctor_id').val();
        if (patient_id === null || attending_doctor_id === null ||
        admission_type === null) {
            alert('Please fill out all the required fields.');
            return false; // Prevent form submission
        }
        else{
            var data = {
                'patient_id' : patient_id,
                'reason_of_admission' : reason_of_admission,
                'admission_type' : admission_type,
                'attending_doctor_id' : attending_doctor_id,
            }
            return data
        }
    }
//  Method for creating new inpatient
    async save_in_patient_data (){
        var data = await this.fetch_in_patient_data()
        if (data != false || data != null || data != undefined){
            this.orm.call('hospital.inpatient','create_new_in_patient',[null,data]
            ).then(function (){
                alert('Inpatient is created');
                  $('#sl_patient_id').val("");
                  $('#reason_of_admission').val("");
                  $('#admission_type').val("");
                  $('#attending_doctor_id').val("");
        });
        }
    }
//  Method for getting room or ward details
    fetchRoomWard (){
        $('#view_secondary').html('');
        this.room_ward.el.classList.remove("d-none")
        this.patient_creation.el.classList.add("d-none");
        this.out_patient.el.classList.add("d-none");
        this.inpatient.el.classList.add("d-none");
        this.rd_buttons.el.classList.add("d-none");
        if ($('.r_active')[0]){$('.r_active')[0].classList.remove('r_active');}
        $('.o_room_ward_button')[0].classList.add('r_active');
    }
//  Method for getting ward details
    async fetchWard (){
        this.ward.el.classList.remove("d-none");
        this.room.el.classList.add("d-none");
        if ($('.r_active2')[0]){$('.r_active2')[0].classList.remove('r_active2');}
        $('.o_ward_button')[0].classList.add('r_active2');
        var result = await this.orm.call('hospital.ward','search_read',)
        this.state.ward_data = result
    }
//  Method for getting room details
    async fetchRoom (){
        this.room.el.classList.remove("d-none");
        this.ward.el.classList.add("d-none");
        if ($('.r_active2')[0]){$('.r_active2')[0].classList.remove('r_active2');}
        $('.o_room_button')[0].classList.add('r_active2');
        var result= await this.orm.call('patient.room','search_read',)
        this.state.room_data = result
    }
}
ReceptionDashBoard.template = "ReceptionDashboard"
registry.category('actions').add('reception_dashboard_tags', ReceptionDashBoard);
