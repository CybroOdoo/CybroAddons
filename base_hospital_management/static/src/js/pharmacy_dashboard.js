/** @odoo-module */
import { registry } from '@web/core/registry';
import { user } from "@web/core/user";
import { useService } from "@web/core/utils/hooks";
import { Component, onWillStart, proxy, signal } from "@odoo/owl";
import { PharmacyOrderLines } from "./pharmacy_orderlines";

export class PharmacyDashboard extends Component {
    setup() {
        super.setup();
        this.vaccine_div = signal.ref();
        this.medicine_div = signal.ref();
        this.home_content = signal.ref();
        this.PatientSearch = signal.ref();
        this.orders_div = signal.ref();
        this.orm = useService('orm')
        this.user = user;
        this.actionService = useService("action");
        this.state = proxy({
            product_lst: [],
            medicines: [],
            units: [],
            sub_total: 0,
            vaccine: [],
            order_data: [],
            order_line: [],
            menu: 'home',
        });
        this.selected_patient_id = false;
        this.selected_patient_code = '';
        this.selected_patient_name = '';
        this.fetch_product();
        onWillStart(async () => {
            this.state.med = await this.orm.call('product.template', 'action_get_medicine_data', []);
        });
    }

    // Fetch product details
    async fetch_product() {
        const domain = [['medicine_ok', '=', true]];
        const result = await this.orm.call('product.template', 'search_read', [domain]);
        this.state.product_lst = result;
        this.create_order();
    }

    // Method for creating sale order
    async create_order() {
        this.state.menu = 'home';
        await this.orm.call('hospital.pharmacy', 'company_currency', [])
            .then((result) => {
                const currencyElements = document.querySelectorAll('[id^="symbol"]');
                currencyElements.forEach(el => {
                    el.textContent = result || '';
                });
            });
        this.state.medicines = this.state.product_lst || [];
    }

    // To update the orderline of sale order
    updateOrderLine(line, id) {
        const orderline = this.state.order_line.find(orderline => orderline.id === id);
        if (orderline) {
            orderline.product = line.product;
            orderline.qty = parseInt(line.qty) || 0;
            orderline.uom = line.uom;
            orderline.price = line.price;
            orderline.sub_total = line.sub_total;
        }
    }

    // To add new row in the sale order line
    addRow() {
        const newLine = proxy({
            id: Date.now() + Math.random(),
            product: false,
            qty: 1,
            uom: false,
            price: 0,
            sub_total: 0
        });
        const data = [...this.state.order_line, newLine];
        this.state.order_line = data;
    }

    // To remove the line if not needed
    removeLine(id) {
        const filteredData = this.state.order_line.filter(line => line.id != id);
        this.state.order_line = filteredData;
    }

    // Create sale order
    async create_sale_order() {
        const nameElement = document.getElementById('patient-name');
        const emailElement = document.getElementById('patient-mail');
        const phoneElement = document.getElementById('patient-phone');
        const dobElement = document.getElementById('o_patient-dob');

        const nameVal = nameElement ? nameElement.value.trim() : '';
        if (!nameVal) {
            alert("Please enter the Name");
            return;
        }

        // If the user modified the name and it doesn't match the searched patient, reset tracked patient
        if (this.selected_patient_name && nameVal.toLowerCase() !== this.selected_patient_name.toLowerCase()) {
            this.selected_patient_id = false;
            this.selected_patient_code = '';
        }

        // Only enforce email when creating a brand new patient
        if (!this.selected_patient_id && (!emailElement || emailElement.value.trim() === "")) {
            alert("Please enter the Email");
            return;
        }

        if (!this.state.order_line || this.state.order_line.length === 0) {
            alert("Please add at least one medicine line.");
            return;
        }

        let hasInvalidQuantity = false;
        for (let line of this.state.order_line) {
            if (line.qty < 1) {
                hasInvalidQuantity = true;
                break;
            }
        }

        if (hasInvalidQuantity) {
            alert('Medicine quantity must be greater than or equal to 1.');
            return;
        }

        const data = {};
        data['name'] = nameVal;
        data['phone'] = phoneElement ? phoneElement.value.trim() : '';
        data['email'] = emailElement ? emailElement.value.trim() : '';
        data['dob'] = dobElement ? dobElement.value : '';
        data['patient_id'] = this.selected_patient_id || false;
        data['patient_code'] = this.selected_patient_code || document.getElementById('patient-code')?.innerText?.trim() || '';
        data['products'] = this.state.order_line;

        const genderRadios = document.getElementsByName('gender');
        data['gender'] = 'male';
        for (let radio of genderRadios) {
            if (radio.checked) {
                data['gender'] = radio.value;
                break;
            }
        }

        try {
            const result = await this.orm.call('hospital.pharmacy', 'create_sale_order', [data]);
            alert('The sale order has been created with reference number ' + result.invoice);
            window.location.reload();
        } catch (error) {
            alert('Error creating sale order: ' + error.message);
        }
    }

    onSearchKeyup(ev) {
        if (ev.key === 'Enter') {
            this.fetch_patient_data();
        }
    }

    // Fetch patient data
    async fetch_patient_data() {
        const searchEl = document.getElementById('patient_search') || this.PatientSearch?.el;
        const patientSearchVal = searchEl ? searchEl.value.trim() : '';
        if (!patientSearchVal) {
            alert("Please enter a patient code");
            return;
        }
        try {
            const result = await this.orm.call(
                'res.partner',
                'action_get_patient_data',
                [patientSearchVal]
            );
            const patientTitle = document.getElementById('patient-title');
            if (patientTitle) {
                patientTitle.innerText = result.name || 'Patient Not Found';
            }
            const patientCodeEl = document.getElementById('patient-code');
            if (patientCodeEl) {
                patientCodeEl.innerText = result.unique || '';
            }
            const patientGenderDisplay = document.getElementById('patient-gender');
            if (patientGenderDisplay) {
                patientGenderDisplay.innerText = result.gender || '';
            }
            const patientBlood = document.getElementById('patient-blood');
            if (patientBlood) {
                patientBlood.innerText = result.blood_group || '';
            }
            const patientImage = document.getElementById('patient-image');
            if (patientImage) {
                if (result.image_1920) {
                    patientImage.src = 'data:image/png;base64,' + result.image_1920;
                } else {
                    patientImage.src = 'https://cdn.pixabay.com/photo/2015/10/05/22/37/blank-profile-picture-973460_1280.png';
                }
            }

            if (result.name && result.name !== 'Patient Not Found') {
                this.selected_patient_id = result.id || false;
                this.selected_patient_code = result.unique || '';
                this.selected_patient_name = result.name;

                const nameInput = document.getElementById('patient-name');
                if (nameInput) nameInput.value = result.name;

                const phoneInput = document.getElementById('patient-phone');
                if (phoneInput) phoneInput.value = result.phone || '';

                const emailInput = document.getElementById('patient-mail');
                if (emailInput) emailInput.value = result.email || '';

                const dobInput = document.getElementById('o_patient-dob');
                if (dobInput) dobInput.value = result.dob || '';

                const patientGender = (result.gender_raw || result.gender || '').toLowerCase();
                if (patientGender) {
                    const genderRadios = document.getElementsByName('gender');
                    genderRadios.forEach(radio => {
                        radio.checked = (radio.value === patientGender);
                    });
                }
            } else {
                this.selected_patient_id = false;
                this.selected_patient_code = '';
                this.selected_patient_name = '';
                const histHead = document.getElementById('hist_head');
                if (histHead) histHead.innerHTML = '';
                alert("Patient Not Found");
            }
        } catch (error) {
            alert('Error fetching patient data: ' + error.message);
        }
    }

    // Fetch medicine data while clicking Medicine button
    async fetch_medicine_data() {
        this.state.menu = 'medicines';
    }

    // Fetch vaccine data
    async fetch_vaccine_data() {
        this.state.menu = 'vaccines';
        this.state.vaccine = await this.orm.call('product.template', 'action_get_vaccine_data', []);
    }

    // Method for fetching all sale orders
    async fetch_sale_orders() {
        this.state.menu = 'orders';
        this.state.order_data = await this.orm.call('sale.order', 'search_read',
            [[['partner_id.patient_seq', 'not in', ['New', 'Employee', 'User']]], ['name', 'create_date', 'partner_id', 'amount_total', 'state']]);
    }

    // Method for emptying the data
    async clear_data() {
        this.selected_patient_id = false;
        this.selected_patient_code = '';
        this.selected_patient_name = '';

        const searchEl = document.getElementById('patient_search') || this.PatientSearch?.el;
        if (searchEl) searchEl.value = '';
        const histHead = document.getElementById('hist_head');
        if (histHead) histHead.innerHTML = '';
        const patientTitle = document.getElementById('patient-title');
        if (patientTitle) patientTitle.textContent = '';
        const patientCodeEl = document.getElementById('patient-code');
        if (patientCodeEl) patientCodeEl.textContent = '';
        const patientGenderDisplay = document.getElementById('patient-gender');
        if (patientGenderDisplay) patientGenderDisplay.textContent = '';
        const patientBlood = document.getElementById('patient-blood');
        if (patientBlood) patientBlood.textContent = '';
        const patientImage = document.getElementById('patient-image');
        if (patientImage) patientImage.src = 'https://cdn.pixabay.com/photo/2015/10/05/22/37/blank-profile-picture-973460_1280.png';

        const nameInput = document.getElementById('patient-name');
        if (nameInput) nameInput.value = '';
        const phoneInput = document.getElementById('patient-phone');
        if (phoneInput) phoneInput.value = '';
        const emailInput = document.getElementById('patient-mail');
        if (emailInput) emailInput.value = '';
        const dobInput = document.getElementById('o_patient-dob');
        if (dobInput) dobInput.value = '';

        const genderRadios = document.getElementsByName('gender');
        genderRadios.forEach(radio => {
            radio.checked = (radio.value === 'male');
        });
    }
}

PharmacyDashboard.template = "PharmacyDashboard"
PharmacyDashboard.components = { PharmacyOrderLines }

registry.category("actions").add('pharmacy_dashboard_tags', PharmacyDashboard);
