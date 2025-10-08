odoo.define('event_seat_booking.register', function (require) {
    'use strict';

    var core = require('web.core');
    var event = require('website_event.website_event');
    var _t = core._t;
    var ajax = require('web.ajax');

    event.include({
        init: function () {
            this._super.apply(this, arguments); // Call the parent's init method if needed
        },
        //Handles the click event on the registration form, processes the form data, and makes an AJAX request
        // to submit the form. It also includes additional logic for seat booking.
        on_click: function (ev) {
        ev.preventDefault();
        ev.stopPropagation();
        var $form = $(ev.currentTarget).closest('form');
        var $target = $(ev.currentTarget);
        var $button = $(ev.currentTarget).closest('[type="submit"]');
        var post = {};
        $('#registration_form table').siblings('.alert').remove();
        $('#registration_form select').each(function () {
            post[$(this).attr('name')] = $(this).val();
            console.log(post,"VALUES")
        });
        var tickets_ordered = _.some(_.map(post, function (value, key) { return parseInt(value); }));
        if (!tickets_ordered) {
            $('<div class="alert alert-info"/>')
                .text(_t('Please select at least one ticket.'))
                .insertAfter('#registration_form table');
            return new Promise(function () {});
        } else {
            var uniqueId = $('#unique_column_id').val();
            if (!uniqueId) {
                    this._super(ev);
                    return;
                }

            var columnNumbers = $('#col_number_id').val(); //
            var rowNumbers = $('#row_number_id').val();

            var colNumbers = columnNumbers.match(/C(\d+)/g).map(e => e.substring(1)); // ['2', '3']
            var rowNumbersExtracted = rowNumbers.match(/R(\d+)/g).map(e => e.substring(1)); // ['4', '4']

            post['unique_id'] = uniqueId;
            post['row_no'] = rowNumbersExtracted;
            post['column_no'] = colNumbers;

            var colNumbers = columnNumbers.match(/C(\d+)/g).map(e => e.substring(1)); // ['2', '3']
            var rowNumbersExtracted = rowNumbers.match(/R(\d+)/g).map(e => e.substring(1)); // ['4', '4']
            $button.attr('disabled', true);
            var action = $form.data('action') || $form.attr('action');
            return ajax.jsonRpc(action, 'call', post).then(function (modal) {
                var $modal = $(modal);
                $modal.find('.modal-body > div').removeClass('container'); // retrocompatibility - REMOVE ME in master / saas-19
                const hidden_div = $modal.find('.ticket_essentials')[0]
                const $hiddenDiv = $(hidden_div);
                const rowNumberInput = $hiddenDiv.find('input[name="row_number"]')[0];
                const columnNumberInput = $hiddenDiv.find('input[name="column_number"]')[0];
                const uniqueIdInput = $hiddenDiv.find('input[name="unique_id"]')[0];

                $modal.appendTo(document.body);
                const modalBS = new Modal($modal[0], {backdrop: 'static', keyboard: false});
                modalBS.show();
                $modal.appendTo('body').modal('show');
                $modal.on('click', '.js_goto_event', function () {
                    $modal.modal('hide');
                    $button.prop('disabled', false);
                });
                $modal.on('click', '.btn-close', function () {
                    $button.prop('disabled', false);
                });
            });
        }
           },

    });
});


