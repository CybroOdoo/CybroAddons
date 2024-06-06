/** @odoo-module */
import { registry} from '@web/core/registry';
import { useRef } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";
import { _t } from "@web/core/l10n/translation";
const { Component, onWillStart, useState} = owl
import { PharmacyOrderLines } from "./pharmacy_orderlines";
    var currency=0;
    var quantity=0;
    var amount=0;
    var sub_t=0;
    var sub_total=0;
    var product_lst=[];
    var uom_lst= [];
    var invoice=0;
    var invoice_id=0;
    var tax=0;
export class PharmacyDashboard extends Component {
//Initialize Pharmacy Dashboard
    setup() {
        super.setup(...arguments);
        this.ref = useRef('root')
        this.vaccine_div = useRef('vaccine_div')
        this.medicine_div = useRef('medicine_div')
        this.home_content = useRef('home_content')
        this.patient_name = useRef('PatientName');
        this.patient_email = useRef('Email');
        this.patient_search = useRef('PatientSearch');
        this.orders_div = useRef('orders_div')
        this.orm = useService('orm')
        this.user = useService("user");
        this.actionService = useService("action");
        this.state = useState({
              product_lst :[],
              medicines :[],
              units :[],
              sub_total,
              vaccine :[],
              order_data:[],
              order_line: [],
              menu: 'home',
        });
        this.fetch_product();
        onWillStart(async () => {
            this.state.med = await this.orm.call('product.template','action_get_medicine_data',[],)})
    }
//  Fetch product details
    async fetch_product() {
        const domain = [['medicine_ok', '=', true]];
        const result = await this.orm.call('product.template', 'search_read', [domain]);
        this.state.product_lst = result;
        this.create_order();
    }
//  Method for creating sale order
    async create_order() {
        this.vaccine_div?.el?.classList.add("d-none");
        this.medicine_div?.el?.classList.add("d-none");
        this.home_content?.el?.classList.remove("d-none");
        this.orders_div?.el?.classList.add("d-none");
        await this.orm.call('hospital.pharmacy','company_currency',
        ).then(function (result){
           $('#symbol'+ currency).text(result || '');
           $('#symbol').text(result || '');
        })
        this.state.medicines = await this.product_lst;
        this.state.units = await this.uom_lst;
    }
// To update the orderline of sale order
    updateOrderLine(line, id) {
        const orderline = this.state.order_line.filter(orderline => orderline.id === id)[0]
        orderline.product = line.product
        orderline.qty = parseInt(line.qty)
        orderline.uom = line.uom
        orderline.price = line.price
        orderline.sub_total = line.sub_total
    }
//  To add new row in the sale order line
    addRow () {
        const data = [...this.state.order_line, owl.reactive({id: new Date(), product: false, qty: 1, uom: 0, price: 0, sub_total: 0})]
        this.state.order_line = data
    }
// To remove the line if not needed
    removeLine(id){
        const filteredData = this.state.order_line.filter(line => line.id != id)
        this.state.order_line = filteredData
    }
//  Create sale order
    async create_sale_order () {
        var data ={};
        data['name'] = $('#patient-name').val();
        data['phone'] = $('#patient-phone').val();
        data['email']=  $('#patient-mail').val();
        data['dob'] =  $('#patient-dob').val();
        data['products']= this.state.order_line;
        let hasInvalidQuantity = false;
        if (hasInvalidQuantity) {
            alert('Medicine quantity must be greater than or equal to 1.');
            return;
        }
        if(this.patient_name.el.value === "")
        {
            alert("Please enter the Name")
            return;
        }
        if(this.patient_email.el.value === "")
        {
            alert("Please enter the Email")
            return;
        }
        this.orm.call('hospital.pharmacy', 'create_sale_order',[data]
        ).then(function (result) {
            alert('The sale order has been created with refernce number ' +result.invoice)
            window.location.reload()
        })
    }
//  Fetch patient data
    async fetch_patient_data () {
        var self = this;
        await this.orm.call('res.partner', 'action_get_patient_data',
           [[this.patient_search.el.value]],
        ).then(function (result) {
            $('#patient-title').text(result.name || '');
            $('#patient-code').text(result.unique || '');
            $('#patient-age').text(result.dob || '');
            $('#patient-blood').text(result.blood_group || '');
            $('#patient-blood').text(result.blood_group || '');
            $('#patient-gender').text(result.gender || '');
            $('#patient-image').attr('data:image/png;base64, ' + result.image_1920);
            if (result.name == 'Patient Not Found') {
               $('#hist_head').html('')
               $('#patient-image').attr('src', 'https://cdn.pixabay.com/photo/2015/10/05/22/37/blank-profile-picture-973460_1280.png');
            }
            else {
            }
        })
    }
//  Fetch medicine data while clicking Medicine button
    async fetch_medicine_data () {
        this.vaccine_div?.el?.classList.add("d-none");
        this.home_content?.el?.classList.add("d-none");
        this.medicine_div?.el?.classList.remove("d-none");
        this.orders_div?.el?.classList.add("d-none");
    }
//  Fetch vaccine data
    async fetch_vaccine_data () {
        this.vaccine_div?.el?.classList.remove("d-none");
        this.home_content?.el?.classList.add("d-none");
        this.medicine_div?.el?.classList.add("d-none");
        this.orders_div?.el?.classList.add("d-none");
        this.state.vaccine = await this.orm.call('product.template','action_get_vaccine_data', [],)
    }
//  Method fo fetching all sale orders
    async fetch_sale_orders () {
        this.vaccine_div?.el?.classList.add("d-none");
        this.home_content?.el?.classList.add("d-none");
        this.medicine_div?.el?.classList.add("d-none");
        this.orders_div?.el?.classList.remove("d-none");
        this.state.order_data = await this.orm.call('sale.order', 'search_read',
            [[['partner_id.patient_seq','not in', ['New', 'Employee', 'User']]], ['name', 'create_date', 'partner_id', 'amount_total', 'state']],)

    }
//  Method for emptying the data
    async clear_data () {
        this.patient_search.el.value = '';
        $('#hist_head').html('')
        $('#patient-title').html('')
        $('#patient-code').html('')
        $('#patient-gender').html('')
        $('#patient-blood').html('')
        $('#patient-image').attr('src', 'https://cdn.pixabay.com/photo/2015/10/05/22/37/blank-profile-picture-973460_1280.png');
    }
}
PharmacyDashboard.template = "PharmacyDashboard"
registry.category("actions").add('pharmacy_dashboard_tags', PharmacyDashboard);
PharmacyDashboard.components = { PharmacyOrderLines }
