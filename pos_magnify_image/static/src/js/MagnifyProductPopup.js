import { Dialog } from "@web/core/dialog/dialog";
import { Component } from "@odoo/owl";

//Created product magnifying widget
export class MagnifyProductPopup extends Component {
    static template = "MagnifyProductPopup";
    static components = { Dialog };
}
