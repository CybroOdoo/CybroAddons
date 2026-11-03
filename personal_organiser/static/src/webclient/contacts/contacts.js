/** @odoo-module **/
import { Component,proxy } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";

export class OrgContacts extends Component {
    "component to manage all the contacts"
    static template = 'personal_organiser.orgcontacts';
    setup() {
        this.orm = useService("orm");
        this.state = proxy({
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
                                               ['name', 'email']);
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

            await this.orm.create('res.partner', [contactData]);
            this.state.name = '';
            this.state.email = '';
            this.state.showInputFields = false;
            await this.fetchContacts();  // show the new contact in the list
        } catch (error) {
            console.error('Error creating contact:', error);
        }
    }
}
