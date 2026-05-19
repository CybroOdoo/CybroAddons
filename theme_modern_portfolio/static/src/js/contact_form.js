/** @odoo-module **/

import publicWidget from "@web/legacy/js/public/public_widget";

publicWidget.registry.ContactForm = publicWidget.Widget.extend({
    selector: '.s_contact_form',
    events: {
        'click .source-field .dropdown-option': '_onSourceClick',
        'click .timeline-field .dropdown-option': '_onTimelineClick',
        'click .discuss-field .dropdown-option': '_onDiscussClick',
    },

    _onSourceClick(ev) {
        this._clicked('source_input', ev);
    },
    _onTimelineClick(ev) {
        this._clicked('timeline_input', ev);
    },
    _onDiscussClick(ev) {
        this._clicked('discuss_input', ev);
    },

    _clicked(id, ev) {
        this.el.querySelector(`#${id}`).value = ev.target.innerText;
    },
});