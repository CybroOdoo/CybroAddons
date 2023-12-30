//// Import the necessary dependencies
//import { useService } from '@odoo/owl';
//import { useRef } from '@odoo/owl';
//
//class YourComponent {
//    setup() {
//        this.orm = useService('orm');
//        this.preview = useRef('preview_modal');
//        this._super.apply(this, arguments);
//
//        // Call a method to open the modal
//        this.openModal();
//    }
//
//    openModal() {
//        // Assuming you are using Bootstrap, trigger the modal by its ID
//        const modal = new bootstrap.Modal(document.getElementById('preview_modal'));
//        modal.show();
//    }
//}
//
//export default YourComponent;
