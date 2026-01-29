odoo.define('odoo_mail_management.odoo_mail', function (require) {
    'use strict';
    var AbstractAction = require('web.AbstractAction');
    var core = require('web.core');
    var rpc = require('web.rpc');
    var OdooMail = AbstractAction.extend({
        template: 'OdooMail',
        events: {
            'click .sent': 'sent_mail',    /*to showing sent mail*/
            'click #all_mail': 'all_mail', /*to show all mail*/
            'click .outbox': 'outbox_mail', /*to show mails in outbox*/
            'click #delete': 'delete_mail',/*to delete selected mail*/
            'click .message-default': 'open_mail',/*to open selected mail*/
            'click #not_starred': 'star_mail', /*to make mail starred*/
            'click #starred': 'unstar_mail', /*to make mail not starred*/
            'click #starred_mails': 'get_starred_mails', /*to get starred mails*/
            'click .google_calender': 'redirect_calender',/*to redirect into calender*/
            'click .keep_note': 'redirect_note',/*to redirect into notes*/
            'click .contacts': 'redirect_contacts',/*to redirect into contact*/
            'click #archive': 'archive_mail',/*to archive mail*/
            'click #archived_mails': 'get_archived_mail',/*to show archived mails*/
            'submit .form_submit': 'send_mail',/*to compose mail*/
            'submit .large_form_submit': 'send_large_mail',/*to compose mail from large modal*/
            'click #unarchive': 'unarchive_mail',/*to make mail  unarchived */
            'click .refresh': 'refresh_page',/*to refresh home page*/
            'click #checkall': 'checkall_mail',/*to check all mail*/
            'click .checkbox_func': 'show_delete_button',/*to show delete button and archive button*/
            'click .delete_checked': 'delete_checked',/*delete checked mail*/
            'keyup .header-search-input': 'search_mail',/*to search mails*/
            'click .archive_checked': 'archive_checked',/*to archive checked*/
            'click #file-input': 'attachment_action',/*to attach file*/
            'click #resend': 'resend_mail',/*to retry mails in outbox*/
            'click #minimizeButton' : 'minimize',
        },
        init: function (parent, action) {
            this._super(parent, action);
        },
        start: function () {
            var self = this;
            self.load_logo()
            self.load_mails()
            self.get_count()
        },
        /*To load logo */
        load_logo: function () {
            rpc.query({
                model: 'mail.icon',
                method: "load_logo",
            }).then(function (result) {
                $(".header-group").append(
                    '<a href="#" class="header-logo">'
                    + '<img src="data:image/png;base64,'+ result + '"'
                    + 'style="width: 100px; margin-left: 36px; margin-bottom: -15px; margin-top: -14px; height: 50px;"/>'
                    + '</a>'
                )
            })
        },
        /*To load mail */
        load_mails: function () {
            rpc.query({
                model: "mail.mail",
                method: "get_all_mails",
            }).then(function (result) {
                $(".mail").empty()
                $(".checkbox_delete").hide()
                $(".checkbox_archive").hide()
                $.each(result, function (index, name) {
                    $(".mail").append(
                        '<div class="inbox-message-item  message-default-unread" data-id="' + name.id + '">'
                        + '<div class="checkbox" style="margin-right: -12px;">'
                        + '<button class="btn">'
                        + '<input type="checkbox" id="checkbox" data-id="' + name.id + '" class="checkbox checkbox_func">'
                        + '</button>'
                        + '</div>'
                        + '<div>'
                        + '<button class="btn star" data-id="' + name.id + '" style="margin: 0;">'
                        + '<img src="/odoo_mail_management/static/src/img/star_border_black_24dp.svg" alt="Not starred" data-id="' + name.id + '" class="btn-icon-sm btn-icon-alt btn-icon-hover message-btn-icon" id="not_starred"/>'
                        + '</button>'
                        + '</div>'
                        + '<div class="message-default" data-id="' + name.id + '">'
                        + '<div class="message-sender message-content">'
                        + '<span>' + name.sender + '</span>'
                        + '</div>'
                        + '<div class="message-subject message-content">'
                        + '<span>' + name.subject + '</span>'
                        + '</div>'
                        + '<div class="message-seperator message-content">-</div>'
                        + '<div class="message-body message-content">'
                        + '<span>' + name.subject + '</span>'
                        + '</div>'
                        + '<div class="gap message-content">&nbsp;</div>'
                        + '<div class="message-date center-text">'
                        + '<span style="margin-left: 500px;">' + name.date + '</span>'
                        + '</div>'
                        + '</div>'
                        + '<div class="message-group-hidden">'
                        + '<div class="inbox-message-item-options">'
                        + '<button class="btn">'
                        + '<img src="/odoo_mail_management/static/src/img/archive_black_24dp.svg" alt="Archive" data-id="' + name.id + '" class="btn-icon-sm btn-icon-alt btn-icon-hover" id="archive"/>'
                        + '</button>'
                        + '<button class="btn">'
                        + '<img src="/odoo_mail_management/static/src/img/delete_black_24dp.svg" alt="Delete" data-id="' + name.id + '" class="btn-icon-sm btn-icon-alt btn-icon-hover" id="delete"/>'
                        + '</button>'
                        + '</div>'
                        + '</div>'
                        + '</div>')
                })
            })
        },
        /*To get count */
        get_count: function () {
            rpc.query({
                model: "mail.mail",
                method: "get_mail_count",
            }).then(function (result) {
                $('.outbox_count').empty()
                $('.all_count').empty()
                $('.sent_count').empty()
                $('.starred_count').empty()
                $('.archived_count').empty()
                $('.outbox_count').append(result.outbox_count)
                $('.all_count').append(result.all_count)
                $('.sent_count').append(result.sent_count)
                $('.starred_count').append(result.starred_count)
                $('.archived_count').append(result.archived_count)
            })
        },
        /*To show all mail*/
        all_mail: function () {
            var self = this;
            self.load_mails()
            $('#sent').removeClass('active')
            $('#archived_mails').removeClass('active')
            $('#outbox').removeClass('active')
            $('#starred_mails').removeClass('active')
            $('#all_mail').addClass('active')
            self.get_count()
        },
        /*To show sent mail*/
        sent_mail: function (e) {
            var self = this;
            $('#outbox').removeClass('active')
            $('#starred_mails').removeClass('active')
            $('#all_mail').removeClass('active')
            $('#archived_mails').removeClass('active')
            $("#sent").addClass("active")
            $(".mail").empty()
            rpc.query({
                model: "mail.mail",
                method: "get_sent_mail",
            }).then(function (result) {
                $.each(result, function (index, name) {
                    $(".mail").append(
                        '<div class="inbox-message-item  message-default-unread" data-id="' + name.id + '">'
                        + '<div class="checkbox" style="margin-right: -12px;">'
                        + '<button class="btn">'
                        + '<input type="checkbox" id="checkbox" data-id="' + name.id + '" class="checkbox checkbox_func">'
                        + '</button>'
                        + '</div>'
                        + '<div>'
                        + '<button class="btn star" data-id="' + name.id + '" style="margin: 0;">'
                        + '<img src="/odoo_mail_management/static/src/img/star_border_black_24dp.svg" alt="Not starred" data-id="' + name.id + '" class="btn-icon-sm btn-icon-alt btn-icon-hover message-btn-icon" id="not_starred"/>'
                        + '</button>'
                        + '</div>'
                        + '<div class="message-default" data-id="' + name.id + '">'
                        + '<div class="message-sender message-content">'
                        + '<span>' + name.sender + '</span>'
                        + '</div>'
                        + '<div class="message-subject message-content">'
                        + '<span>' + name.subject + '</span>'
                        + '</div>'
                        + '<div class="message-seperator message-content">-</div>'
                        + '<div class="message-body message-content">'
                        + '<span>' + name.subject + '</span>'
                        + '</div>'
                        + '<div class="gap message-content">&nbsp;</div>'
                        + '<div class="message-date center-text">'
                        + '<span style="margin-left: 500px;">' + name.date + '</span>'
                        + '</div>'
                        + '</div>'
                        + '<div class="message-group-hidden">'
                        + '<div class="inbox-message-item-options">'
                        + '<button class="btn">'
                        + '<img src="/odoo_mail_management/static/src/img/archive_black_24dp.svg" alt="Archive" data-id="' + name.id + '" class="btn-icon-sm btn-icon-alt btn-icon-hover" id="archive"/>'
                        + '</button>'
                        + '<button class="btn">'
                        + '<img src="/odoo_mail_management/static/src/img/delete_black_24dp.svg" alt="Delete" data-id="' + name.id + '" class="btn-icon-sm btn-icon-alt btn-icon-hover" id="delete"/>'
                        + '</button>'
                        + '</div>'
                        + '</div>'
                        + '</div>')
                    self.get_count()
                })
            })
        },
        /*To show mails in outbox*/
        outbox_mail: function () {
            var self = this;
            $('#all_mail').removeClass('active')
            $("#sent").removeClass("active")
            $('#archived_mails').removeClass('active')
            $('#starred_mails').removeClass('active')
            $('#outbox').addClass('active')
            $(".mail").empty()
            rpc.query({
                model: "mail.mail",
                method: "get_outbox_mail",
            }).then(function (result) {
                $.each(result, function (index, name) {
                    $(".mail").append(
                        '<div class="inbox-message-item  message-default-unread" data-id="' + name.id + '" >'
                        + '<div class="checkbox" style="margin-right: -12px;">'
                        + '<button class="btn">'
                        + '<input type="checkbox" id="checkbox" data-id="' + name.id + '" class="checkbox checkbox_func">'
                        + '</button>'
                        + '</div>'
                        + '<div>'
                        + '<button class="btn star" data-id="' + name.id + '" style="margin: 0;">'
                        + '<img src="/odoo_mail_management/static/src/img/star_border_black_24dp.svg" alt="Not starred" data-id="' + name.id + '" class="btn-icon-sm btn-icon-alt btn-icon-hover message-btn-icon" id="not_starred"/>'
                        + '</button>'
                        + '</div>'
                        + '<div class="message-default" data-id="' + name.id + '">'
                        + '<div class="message-sender message-content">'
                        + '<span id="sender">' + name.sender + '</span>'
                        + '</div>'
                        + '<div class="message-subject message-content">'
                        + '<span>' + name.subject + '</span>'
                        + '</div>'
                        + '<div class="message-seperator message-content">-</div>'
                        + '<div class="message-body message-content">'
                        + '<span>' + name.subject + '</span>'
                        + '</div>'
                        + '<div class="gap message-content">&nbsp;</div>'
                        + '<div class="message-date center-text">'
                        + '<span style="margin-left: 500px;">' + name.date + '</span>'
                        + '</div>'
                        + '</div>'
                        + '<div class="message-group-hidden">'
                        + '<div class="inbox-message-item-options">'
                        + '<button class="btn">'
                        + '<img src="/odoo_mail_management/static/src/img/archive_black_24dp.svg" alt="Archive" data-id="' + name.id + '" class="btn-icon-sm btn-icon-alt btn-icon-hover" id="archive"/>'
                        + '</button>'
                        + '<button class="btn">'
                        + '<img src="/odoo_mail_management/static/src/img/delete_black_24dp.svg" alt="Delete" data-id="' + name.id + '"   class="btn-icon-sm btn-icon-alt btn-icon-hover" id="delete"/>'
                        + '</button>'
                        + '<button class="btn">'
                        + '<img src="/odoo_mail_management/static/src/img/refresh_black_24dp.svg"" alt="Resend" data-id="' + name.id + '"   class="btn-icon-sm btn-icon-alt btn-icon-hover" id="resend"/>'
                        + '</button>'
                        + '</div>'
                        + '</div>'
                        + '</div>')
                })
                self.get_count()
            })
        },
        /*To get starred mails*/
        get_starred_mails: function () {
            var self = this;
            $('#all_mail').removeClass('active')
            $("#sent").removeClass("active")
            $('#outbox').removeClass('active')
            $('#archived_mails').removeClass('active')
            $('#starred_mails').addClass('active')
            $(".mail").empty()
            rpc.query({
                model: "mail.mail",
                method: "get_starred_mail",
            }).then(function (result) {
                $.each(result, function (index, name) {
                    $(".mail").append(
                        '<div class="inbox-message-item  message-default-unread" data-id="' + name.id + '" >'
                        + '<div class="checkbox" style="margin-right: -12px;">'
                        + '<button class="btn">'
                        + '<input type="checkbox" id="checkbox" data-id="' + name.id + '" class="checkbox checkbox_func">'
                        + '</button>'
                        + '</div>'
                        + '<div>'
                        + '<button class="btn star" data-id="' + name.id + '" style="margin: 0;">'
                        + '<img src="/odoo_mail_management/static/src/img/yellow_star.svg" alt="Not starred" data-id="' + name.id + '" class="btn-icon-sm btn-icon-alt btn-icon-hover message-btn-icon" id="starred"/>'
                        + '</button>'
                        + '</div>'
                        + '<div class="message-default " data-id="' + name.id + '" >'
                        + '<div class="message-sender message-content ">'
                        + '<span id="sender">' + name.sender + '</span>'
                        + '</div>'
                        + '<div class="message-subject message-content">'
                        + '<span>' + name.subject + '</span>'
                        + '</div>'
                        + '<div class="message-seperator message-content">-</div>'
                        + '<div class="message-body message-content">'
                        + '<span>' + name.subject + '</span>'
                        + '</div>'
                        + '<div class="gap message-content">&nbsp;</div>'
                        + '<div class="message-date center-text">'
                        + '<span style="margin-left: 500px;">' + name.date + '</span>'
                        + '</div>'
                        + '</div>'
                        + '<div class="message-group-hidden">'
                        + '<div class="inbox-message-item-options">'
                        + '<button class="btn">'
                        + '<img src="/odoo_mail_management/static/src/img/archive_black_24dp.svg" alt="Archive" data-id="' + name.id + '" class="btn-icon-sm btn-icon-alt btn-icon-hover" id="archive"/>'
                        + '</button>'
                        + '<button class="btn">'
                        + '<img src="/odoo_mail_management/static/src/img/delete_black_24dp.svg" alt="Delete" data-id="' + name.id + '" aria-label="Delete"  class="btn-icon-sm btn-icon-alt btn-icon-hover" id="delete"/>'
                        + '</button>'
                        + '</div>'
                        + '</div>'
                        + '</div>')
                })
                self.get_count()
            })
        },
        /*To show archived mails*/
        get_archived_mail: function (event) {
            var self = this;
            $('#all_mail').removeClass('active')
            $("#sent").removeClass("active")
            $('#outbox').removeClass('active')
            $('#starred_mails').removeClass('active')
            $('#archived_mails').addClass('active')
            $(".mail").empty()
            rpc.query({
                model: "mail.mail",
                method: "get_archived_mail",
            }).then(function (result) {
                $.each(result, function (index, name) {
                    $(".mail").append(
                        '<div class="inbox-message-item  message-default-unread" data-id="' + name.id + '" >'
                        + '<div class="checkbox" style="margin-right: -12px;">'
                        + '<button class="btn">'
                        + '<input type="checkbox" id="checkbox" data-id="' + name.id + '" class="checkbox checkbox_func">'
                        + '</button>'
                        + '</div>'
                        + '<div>'
                        + '</div>'
                        + '<div class="message-default" data-id="' + name.id + '">'
                        + '<div class="message-sender message-content">'
                        + '<span id="sender" style="margin-left: 40px;">' + name.sender + '</span>'
                        + '</div>'
                        + '<div class="message-subject message-content">'
                        + '<span>' + name.subject + '</span>'
                        + '</div>'
                        + '<div class="message-seperator message-content">-</div>'
                        + '<div class="message-body message-content">'
                        + '<span>' + name.subject + '</span>'
                        + '</div>'
                        + '<div class="gap message-content">&nbsp;</div>'
                        + '<div class="message-date center-text">'
                        + '<span style="margin-left: 500px;">' + name.date + '</span>'
                        + '</div>'
                        + '</div>'
                        + '<div class="message-group-hidden">'
                        + '<div class="inbox-message-item-options">'
                        + '<button class="btn">'
                        + '<img src="/odoo_mail_management/static/src/img/unarchive_FILL1_wght400_GRAD0_opsz48.svg" alt="Unarchive" data-id="' + name.id + '" class="btn-icon-sm btn-icon-alt btn-icon-hover" id="unarchive"/>'
                        + '</button>'
                        + '<button class="btn">'
                        + '<img src="/odoo_mail_management/static/src/img/delete_black_24dp.svg" alt="Delete" data-id="' + name.id + '" aria-label="Delete"  class="btn-icon-sm btn-icon-alt btn-icon-hover" id="delete"/>'
                        + '</button>'
                        + '</div>'
                        + '</div>'
                        + '</div>')
                })
                self.get_count()
            })
        },
        /*To archive mail*/
        archive_mail: function (event) {
            var self = this;
            var mail_id = event.currentTarget.attributes[2].value
            rpc.query({
                model: "mail.mail",
                method: "archive_mail",
                args: [mail_id]
            }).then(function () {
                self.get_count()
            })
            $.each($(".inbox-message-item"), function (index, name) {
                if (name.attributes[1].value == mail_id) {
                    name.remove()
                }
            })
        },
        /*To make mail  unarchived */
        unarchive_mail: function (event) {
            var self = this;
            var mail_id = event.currentTarget.attributes[2].value
            rpc.query({
                model: "mail.mail",
                method: "unarchive_mail",
                args: [mail_id]
            }).then(function () {
                self.get_count()
            })
            $.each($(".inbox-message-item"), function (index, name) {
                if (name.attributes[1].value == mail_id) {
                    name.remove()
                }
            })
        },
        /*To check all mail*/
        checkall_mail: function (ev) {
            var check = $("#checkall")
            if (check.is(':checked')) {
                $(".checkbox").prop('checked', true);
                $(".checkbox_delete").show()
                $(".checkbox_archive").show()
            }
            else {
                $(".checkbox").prop('checked', false);
                $(".checkbox_delete").hide()
                $(".checkbox_archive").hide()
            }
        },
        /*To show delete button and archive button*/
        show_delete_button: function (ev) {
            var check = $(".checkbox_func")
            if (check.is(':checked')) {
                $(".checkbox_delete").show()
                $(".checkbox_archive").show()
            }
            else {
                $(".checkbox_delete").hide()
                $(".checkbox_archive").hide()
            }
        },
        /*To archive checked*/
        archive_checked: function (ev) {
            var self = this;
            var check = $(".checkbox_func")
            var ids = []
            $.each(check, function (index, name) {
                if (name.checked) {
                    ids.push((name.attributes[2].value))
                }
            })
            rpc.query({
                model: "mail.mail",
                method: "archive_checked_mail",
                args: [ids]
            }).then(function () {
                self.get_count()
            })
            $.each($(".inbox-message-item"), function (index, name) {
                $.each(ids, function (index, mail_id) {
                    if (name.attributes[1].value == mail_id) {
                        name.remove()
                    }
                })
            })
        },
        /*To delete checked mail*/
        delete_checked: function (ev) {
            var self = this;
            var check = $(".checkbox_func")
            var ids = []
            $.each(check, function (index, name) {
                if (name.checked) {
                    ids.push((name.attributes[2].value))
                }
            })
            $.each($(".inbox-message-item"), function (index, name) {
                $.each(ids, function (index, mail_id) {
                    if (name.attributes[1].value == mail_id) {
                        name.remove()
                    }
                })
            })
            rpc.query({
                model: "mail.mail",
                method: "delete_checked_mail",
                args: [ids]
            }).then(function () {
                self.get_count()
            })
        },
        /*To delete selected mail*/
        delete_mail: function (event) {
            var self = this;
            var id = event.target.attributes[2].value
            rpc.query({
                model: "mail.mail",
                method: "delete_mail",
                args: [id]
            }).then(function () {
                self.get_count()
            })
            $.each($(".inbox-message-item"), function (index, name) {
                if (name.attributes[1].value == id) {
                    name.remove()
                }
            })
        },
        /*To open selected mail*/
        open_mail: function (ev) {
            $(".mail").empty()
            var mail_id = ev.currentTarget.attributes[1].value
            rpc.query({
                model: "mail.mail",
                method: "open_mail",
                args: [mail_id]
            }).then(function (result) {
                $(".mail").append(result)
            })
        },
        /*To make mail starred*/
        star_mail: function (ev) {
            var self = this;
            ev.currentTarget.outerHTML = '<img src="/odoo_mail_management/static/src/img/yellow_star.svg" alt="Not starred"  class="btn-icon-sm btn-icon-alt btn-icon-hover message-btn-icon" id="starred"/>'
            var mail_id = ev.currentTarget.attributes[2].value
            rpc.query({
                model: "mail.mail",
                method: "star_mail",
                args: [mail_id],
            }).then(function () {
                self.get_count()
            })
        },
        /*To make mail not starred*/
        unstar_mail: function (ev) {
            var self = this;
            var mail_id = ev.target.parentElement.attributes[1].value
            ev.target.parentElement.innerHTML = '<img src="/odoo_mail_management/static/src/img/star_border_black_24dp.svg" alt="Not starred" data-id="' + mail_id + '" class="btn-icon-sm btn-icon-alt btn-icon-hover message-btn-icon" id="not_starred" />'
            rpc.query({
                model: "mail.mail",
                method: "unstar_mail",
                args: [mail_id],
            }).then(function () {
                self.get_count()
            })
        },
        /*To redirect into calender*/
        redirect_calender: function (ev) {
            this.do_action({
                name: "Calender",
                type: 'ir.actions.act_window',
                res_model: 'calendar.event',
                view_mode: 'calendar,tree',
                view_type: 'calendar',
                views: [[false, 'calendar'], [false, 'tree']],
                target: 'current',
            })
        },
        /*To redirect into notes*/
        redirect_note: function (ev) {
            this.do_action({
                name: "Notes",
                type: 'ir.actions.act_window',
                res_model: 'note.note',
                view_mode: 'kanban,form,tree,activity',
                view_type: 'kanban',
                views: [[false, 'kanban'], [false, 'form'], [false, 'tree'], [false, 'activity']],
                target: 'current',
            })
        },
        /*To redirect into contact*/
        redirect_contacts: function (ev) {
            this.do_action({
                name: "Contacts",
                type: 'ir.actions.act_window',
                res_model: 'res.partner',
                view_mode: 'kanban,form,tree,activity',
                view_type: 'kanban',
                views: [[false, 'kanban'], [false, 'form'], [false, 'tree'], [false, 'activity']],
                target: 'current',
            })
        },
        /*To attach file*/
        attachment_action: function () {
            this.do_action({
                name: "Mail",
                type: 'ir.actions.act_window',
                res_model: 'mail.attachment',
                view_type: 'form',
                view_mode: 'form',
                views: [[false, 'form']],
                target: 'new',
            })
        },
        /*To refresh home page*/
        refresh_page: function (ev) {
            location.reload()
        },
        /*To search mails*/
        search_mail: function (ev) {
            var value = $('.header-search-input').val().toLowerCase()
            $(".inbox-message-item").filter(function () {
                $(this).toggle($(this).text().toLowerCase().indexOf(value) > -1)
            });
        },
        /*To compose mail from large modal*/
        send_large_mail: function () {
            var self = this
            var subject = $('#l_subject').val()
            var recipient = $('#l_Recipient').val()
            var content = $('#l_content').val()
            rpc.query({
                model: "mail.mail",
                method: "sent_mail",
                args: [{ "subject": subject, "recipient": recipient, "content": content, }]
            }).then(function () {
                self.refresh_page()
            })
        },
        /*To compose mail*/
        send_mail: function () {
            var self = this
            var subject = $("#subject").val()
            var recipient = $("#Recipient").val()
            var content = $("#content").val()
            var file = $('#file-input').val()
            rpc.query({
                model: "mail.mail",
                method: "sent_mail",
                args: [{ "subject": subject, "recipient": recipient, "content": content, }]
            }).then(function () {
                self.refresh_page()
            })
        },
        /*To resend a mail in outbox*/
        resend_mail: function (ev) {
            var self = this
            var mail_id = ev.target.attributes[3].value
            rpc.query({
                model: "mail.mail",
                method: "retry_mail",
                args: [mail_id],
            }).then(function () {
                self.refresh_page()
            })

        },
    });
    core.action_registry.add("odoo_mail", OdooMail);
    return OdooMail;
});
