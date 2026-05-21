/** @odoo-module **/
/**
 * This JavaScript file extends the ListRenderer class from the Odoo web module.
 * It defines a custom ListRenderer called LoginListRenderer for the login_tree_view.
 * The LoginListRenderer adds additional functionality to the rendering of rows in the login_tree_view.
 */
import { ListRenderer } from '@web/views/list/list_renderer';
import { registry } from '@web/core/registry';
import { listView } from '@web/views/list/list_view';
const { onMounted } = owl;

export class LoginListRenderer extends ListRenderer {
    /**
     * Setup method for the LoginListRenderer.
     * It overrides the setup method of the ListRenderer class.
     * This method is called when the component is mounted to the DOM.
     */
    setup() {
        super.setup();
        onMounted(async () => {
            if (this.props.list.resModel === 'res.users.login.attempt') {
                let obj = $.parseHTML("<th id='status_otp_login'></th>");
                let table = this.tableRef.el;
                let tHead = table.querySelector("thead");
                let tBody = table.querySelector("tbody");
                await tHead.children[0].insertBefore(obj[0], tHead.children[0].lastElementChild);
                this.renderRows(tBody);
            }
        });
    }
    /**
     * Render rows method for the LoginListRenderer.
     * It adds icons to the rows based on the login status (Failed or Success).
     * @param {Object} ev - The event object containing the rows.
     */
   renderRows(ev) {
//    _.each(ev.rows, function (row) {
    for (const row of ev.rows) {
//    ev.rows.forEach(function (row) {
        if (row && row.children[2] && row.children[2].textContent == 'Failed') {
            let obj = $.parseHTML('<td><i class="fa fa-exclamation-triangle" style="color:red"></i></td>');
            row.insertBefore(obj[0], row.lastElementChild);
        } else if (row && row.children[2] && row.children[2].textContent == 'Success') {
            let obj = $.parseHTML('<td><i class="fa fa-check" style="color:green"></i></td>');
            row.insertBefore(obj[0], row.lastElementChild);
        }
    }
}
}
// Register the LoginListRenderer with the 'login_tree_view' category
registry.category('views').add('login_tree_view', {
    ...listView,
    Renderer: LoginListRenderer,
});
