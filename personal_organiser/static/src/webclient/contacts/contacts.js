/** @odoo-module **/
import { Component,useState } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";
export class OrgContacts extends Component {
    "component to manage all the contacts"
    static template = 'personal_organiser.orgcontacts';
    setup() {
        this.orm = useService("orm");
        this.state = useState({
            contacts: [],
             name: '',
            email: '',
            showInputFields: false,
        });
        this.fetchContacts();
    }
    async fetchContacts() {
        try {
            this.state.contacts = await this.orm.searchRead("res.partner", [],
                                               ['name', 'email','image_1920']);
        } catch (error) {
            console.error('Error fetching contacts:', error);
        }
    }
     toggleInputFields() {
        this.state.showInputFields = !this.state.showInputFields;
    }

    async createContact() {
        try {
            const contactData = {
                name: this.state.name,
                email: this.state.email,
            };

            const partnerId = await this.orm.create('res.partner', [contactData]);
            this.state.name = '';
            this.state.email = '';
            this.state.showInputFields = false;
        } catch (error) {
            console.error('Error creating contact:', error);
        }
    }
    onClickDiv(event) {
        console.log(event,"event")
        const el = event.srcElement.nextSibling;
        el.style.display = (el.style.display === "block") ? "none" : "block";
    }
}