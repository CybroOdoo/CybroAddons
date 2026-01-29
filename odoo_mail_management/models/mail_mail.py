# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Hafeesul Ali(<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU AFFERO
#    GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
from odoo import api, fields, models


class MailMail(models.Model):
    """ Inherited model representing an extended mail module."""
    _inherit = "mail.mail"

    is_starred = fields.Boolean(string="Starred Mail", default=False,
                                help="Flag indicating whether the mail is "
                                     "starred.")
    is_active = fields.Boolean(default=True, string="Active",
                            help="Flag indicating whether the mail is active.")



    @api.model
    def get_all_mails(self):
        """ Method to load all mail.
        Returns:
            dict: A dictionary of all mails"""
        mail_dict = {}
        mails = self.sudo().search([('create_uid', '=', self.env.user.id)],
                                   order="create_date desc")
        for i in mails:
            if i.email_to:
                mail_dict[str(i.mail_message_id)] = ({
                    "id": i.id,
                    "sender": i.email_to,
                    "subject": i.subject,
                    "date": fields.Date.to_date(i.create_date),
                })
            elif i.recipient_ids:
                mail_dict[str(i.mail_message_id)] = ({
                    "id": i.id,
                    "sender": i.recipient_ids.name,
                    "subject": i.subject,
                    "date": fields.Date.to_date(i.create_date),
                })
        return mail_dict

    @api.model
    def get_mail_count(self):
        """Method to get count of all mails,sent mails
        ,mails in outbox,starred mails and archived mails.
        Returns:
            dict: A dictionary of count of all mails,sent mails,mails in outbox
            ,starred mails and archived mails"""
        all_count = self.sudo().search_count(
            [('create_uid', '=', self.env.user.id)])
        sent_count = self.sudo().search_count(
            [('create_uid', '=', self.env.user.id), ('state', '=', 'sent')])
        outbox_count = self.sudo().search_count(
            [('state', '=', 'exception'),
             ('create_uid', '=', self.env.user.id)])
        stared_count = self.sudo().search_count(
            [('is_starred', '=', True), ('create_uid', '=', self.env.user.id)])
        archived_count = self.sudo().search_count(
            [('is_active', '=', False), ('create_uid', '=', self.env.user.id)])
        mail_dict = {'all_count': all_count,
                     'sent_count': sent_count,
                     'outbox_count': outbox_count,
                     'starred_count': stared_count,
                     "archived_count": archived_count, }
        return mail_dict

    @api.model
    def get_sent_mail(self):
        """Method to get all sent mail.
        Returns:
            dict: A dictionary of all sent mails"""
        mail_dict = {}
        mails = self.sudo().search([('state', '=', 'sent'),
                                    ('create_uid', '=', self.env.user.id)],
                                   order="create_date desc")
        for i in mails:
            if i.email_to:
                mail_dict[str(i.mail_message_id)] = ({
                    "id": i.id,
                    "sender": i.email_to,
                    "subject": i.subject,
                    "date": fields.Date.to_date(i.create_date),
                })
            elif i.recipient_ids:
                mail_dict[str(i.mail_message_id)] = ({
                    "id": i.id,
                    "sender": i.recipient_ids.name,
                    "subject": i.subject,
                    "date": fields.Date.to_date(i.create_date),
                })
            else:
                mail_dict[str(i.mail_message_id)] = ({
                    "id": i.id,
                    "sender": "",
                    "subject": i.subject,
                    "date": fields.Date.to_date(i.create_date),
                })
        return mail_dict

    @api.model
    def get_outbox_mail(self):
        """Method to get all mails in outbox.
        Return:
            dict:A dictionary of all mails in outbox """
        mail_dict = {}
        mails = self.sudo().search(
            [('state', '=', 'exception'),
             ('create_uid', '=', self.env.user.id)],
            order="create_date desc")
        for i in mails:
            if i.email_to:
                mail_dict[str(i.mail_message_id)] = ({
                    "id": i.id,
                    "sender": i.email_to,
                    "subject": i.subject,
                    "date": fields.Date.to_date(i.create_date),
                })
            elif i.recipient_ids:
                mail_dict[str(i.mail_message_id)] = ({
                    "id": i.id,
                    "sender": i.recipient_ids.name,
                    "subject": i.subject,
                    "date": fields.Date.to_date(i.create_date),
                })
            else:
                mail_dict[str(i.mail_message_id)] = ({
                    "id": i.id,
                    "sender": "",
                    "subject": i.subject,
                    "date": fields.Date.to_date(i.create_date),
                })
        return mail_dict

    @api.model
    def get_starred_mail(self):
        """Method to fetch all starred mails.
        Return:
            dict:A dictionary of starred mails"""
        mail_dict = {}
        mails = self.sudo().search(
            [('is_starred', '=', True), ('create_uid', '=', self.env.user.id)])
        for i in mails:
            if i.email_to:
                mail_dict[str(i.mail_message_id)] = ({
                    "id": i.id,
                    "sender": i.email_to,
                    "subject": i.subject,
                    "date": fields.Date.to_date(i.create_date),
                })
            elif i.recipient_ids:
                mail_dict[str(i.mail_message_id)] = ({
                    "id": i.id,
                    "sender": i.recipient_ids.name,
                    "subject": i.subject,
                    "date": fields.Date.to_date(i.create_date),
                })
            else:
                mail_dict[str(i.mail_message_id)] = ({
                    "id": i.id,
                    "sender": "",
                    "subject": i.subject,
                    "date": fields.Date.to_date(i.create_date),
                })
        return mail_dict

    @api.model
    def delete_mail(self, *args):
        """Method to unlink mail."""
        self.sudo().search(
            [('id', '=', *args), ('create_uid', '=', self.env.user.id), '|',
             ('is_active', '=', False), ('id', '=', *args),
             ('create_uid', '=', self.env.user.id)]).sudo().unlink()

    @api.model
    def open_mail(self, *args):
        """Method to open a mail and show its content.
        Args:
            *args(int):ID of the mail that want to open.
        Returns:
            text: body_html of a chosen mail. """
        return self.sudo().search(
            [('id', '=', *args), ('create_uid', '=', self.env.user.id), '|',
             ('is_active', '=', False), ('id', '=', *args),
             ('create_uid', '=', self.env.user.id)]).body_html

    @api.model
    def star_mail(self, *args):
        """Method to make a mail starred.
        Args:
            *args(int):ID of the mail that want to star."""
        self.search([('id', '=', *args),
                     ('create_uid', '=', self.env.user.id)]). \
            write({"is_starred": True})

    @api.model
    def unstar_mail(self, *args):
        """Method to make a mail not starred.
        Args:
            *args(int):ID of the mail that want to make not starred. """
        self.sudo().search([('id', '=', *args),
                            ('create_uid', '=', self.env.user.id)]). \
            write({"is_starred": False})

    @api.model
    def archive_mail(self, *args):
        """Method to archive mail.
        Args:
            *args(int):ID of the mail that want to archive. """
        self.sudo().search([('id', '=', *args),
                            ('create_uid', '=', self.env.user.id)]). \
            write({"is_active": False})

    @api.model
    def get_archived_mail(self):
        """Method to get archived mails
        Returns:
            dict:A dictionary of archived mails. """
        mail_dict = {}
        mails = self.sudo().search([('is_active', '=', False),
                                    ('create_uid', '=', self.env.user.id)])
        for i in mails:
            if i.email_to:
                mail_dict[str(i.mail_message_id)] = ({
                    "id": i.id,
                    "sender": i.email_to,
                    "subject": i.subject,
                    "date": fields.Date.to_date(i.create_date),
                })
            elif i.recipient_ids:
                mail_dict[str(i.mail_message_id)] = ({
                    "id": i.id,
                    "sender": i.recipient_ids.name,
                    "subject": i.subject,
                    "date": fields.Date.to_date(i.create_date),
                })
        return mail_dict

    @api.model
    def unarchive_mail(self, *args):
        """Method to make mail unarchived.
        Args:
            *args(int):The id of the mail to be unarchived."""
        self.sudo().search([('is_active', '=', False), ('id', '=', *args),
                            ('create_uid', '=', self.env.user.id)]). \
            write({'is_active': True})

    @api.model
    def delete_checked_mail(self, *args):
        """Method to delete checked mails.
        Args:
            *args(int):I'd of the mail to be deleted."""
        self.search(
            [('id', 'in', *args), '|', ('id', 'in', *args),
             ('is_active', '=', False)]).sudo().unlink()

    @api.model
    def archive_checked_mail(self, *args):
        """Method to archive checked mails.
        Args:
            *args(int):ID of the checked mails to be archived."""
        self.sudo().search([('id', 'in', *args),
                            ('create_uid', '=', self.env.user.id)]). \
            write({"is_active": False})

    @api.model
    def sent_mail(self, *args):
        """Method to compose and send mail.
        Args:
            *args(dict):A dictionary of mail subject content and recipient."""
        mail_from = self.env.user.email
        for item in args:
            subject = item.get("subject")
            recipient = item.get("recipient")
            content = item.get("content")
        attachment_id = self.env['mail.attachment']. \
            search([], order="id desc", limit=1).id
        if attachment_id:
            mail_attachment = self.env['ir.attachment']. \
                sudo().search(
                [('res_id', '=', attachment_id),
                 ('res_field', '=', 'mail_attachment')], limit=1)
            file_name = self.env['mail.attachment']. \
                sudo().search([], order="id desc", limit=1)
            mail_attachment.sudo().write({
                "name": file_name.file_name
            })
            self.sudo().create({
                "subject": subject,
                "email_to": recipient,
                "email_from": mail_from,
                "body_html": content,
                "attachment_ids": mail_attachment
            })
            self.sudo().search([], limit=1).send()
            self.env['mail.attachment'].sudo().search([]).unlink()
        else:
            self.sudo().create({
                "subject": subject,
                "email_to": recipient,
                "email_from": mail_from,
                "body_html": content,
            })
            self.sudo().search([], limit=1).send()

    @api.model
    def retry_mail(self, *args):
        """Method to retry failed messages"""
        mail = self.search([('id', '=', int(*args)),
                            ('create_uid', '=', self.env.user.id)])
        mail.mark_outgoing()
        mail.send()
