/** @odoo-module **/
import publicWidget from "@web/legacy/js/public/public_widget";

publicWidget.registry.prescriptionWidget = publicWidget.Widget.extend({
    //Extends the publicWidget.Widget class to create prescriptionWidget
    selector: '#my_prescriptions',
    events: {
        'click .pr_download': 'onDownloadClick',
    },
    onDownloadClick: function (ev) {
        var rec_id = $(ev.currentTarget).data('id');
        rpc.query({
            model: 'hospital.outpatient',
            method: 'create_file',
            args: [rec_id],
        }).then(function (result) {
            window.open(result['url']);
        });
    },
});
export default publicWidget.registry.prescriptionWidget;
