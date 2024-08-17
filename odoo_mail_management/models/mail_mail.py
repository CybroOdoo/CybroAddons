# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
import re
from odoo.exceptions import ValidationError



class MailMail(models.Model):
    """This model extends the 'mail.mail' model in Odoo to add additional
     features."""
    _inherit = "mail.mail"

    is_starred = fields.Boolean(string="Starred Mail", default=False,
                                help="Flag indicating whether the mail is"
                                     " starred.")
    active = fields.Boolean(default=True,
                            help="Flag indicating whether the mail is active.")

    @api.model
    def get_mail_count(self):
        """Method to get count of all mails,sent mails
        ,mails in outbox,starred mails and archived mails."""
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
            [('active', '=', False), ('create_uid', '=', self.env.user.id)])
        mail_dict = {'all_count': all_count,
                     'sent_count': sent_count,
                     'outbox_count': outbox_count,
                     'starred_count': stared_count,
                     "archived_count": archived_count, }
        return mail_dict

    @api.model
    def get_starred_mail(self):
        """Method to fetch all starred mails."""
        mails = self.sudo().search(
            [('is_starred', '=', True), ('create_uid', '=', self.env.user.id)])
        return mails.read()

    @api.model
    def delete_mail(self, ids):
        """Method to unlink mail."""
        mails = self.sudo().search(
            [('id', 'in', ids), ('create_uid', '=', self.env.user.id), '|',
             ('active', '=', False), ('id', 'in', ids),
             ('create_uid', '=', self.env.user.id)])
        for mail in mails:
            mail.sudo().unlink()

    @api.model
    def open_mail(self, *args):
        """Method to open a mail and show its content."""
        detail = self.sudo().search(
            [('id', '=', *args), ('create_uid', '=', self.env.user.id), '|',
             ('active', '=', False), ('id', '=', *args),
             ('create_uid', '=', self.env.user.id)]).body_html
        return detail

    @api.model
    def star_mail(self, *args):
        """Method to make a mail starred."""
        self.search([('id', '=', *args),
                     ('create_uid', '=', self.env.user.id)]). \
            write({"is_starred": True})

    @api.model
    def unstar_mail(self, *args):
        """Method to make a mail not starred."""
        self.sudo().search([('id', '=', *args),
                            ('create_uid', '=', self.env.user.id)]). \
            write({"is_starred": False})

    @api.model
    def archive_mail(self, *args):
        """Method to archive mail."""
        self.sudo().search([('id', '=', *args),
                            ('create_uid', '=', self.env.user.id)]). \
            write({"active": False})

    @api.model
    def get_archived_mail(self):
        """Method to get archived mails"""
        mail_dict = {}
        mails = self.sudo().search([('active', '=', False),
                                    ('create_uid', '=', self.env.user.id)])
        for record in mails:
            if record.email_to:
                mail_dict[str(record.mail_message_id)] = ({
                    "id": record.id,
                    "sender": record.email_to,
                    "subject": record.subject,
                    "date": fields.Date.to_date(record.create_date), })
            elif record.recipient_ids:
                mail_dict[str(record.mail_message_id)] = ({
                    "id": record.id,
                    "sender": record.recipient_ids.name,
                    "subject": record.subject,
                    "date": fields.Date.to_date(record.create_date), })
        return mails.read()

    @api.model
    def unarchive_mail(self, *args):
        """Method to make mail unarchived."""
        self.sudo().search([('active', '=', False), ('id', '=', *args),
                            ('create_uid', '=', self.env.user.id)]). \
            write({'active': True})

    @api.model
    def delete_checked_mail(self, *args):
        """Method to delete checked mails."""
        self.search(
            [('id', '=', *args), '|', ('id', '=', *args),
             ('active', '=', False)]).sudo().unlink()

    @api.model
    def archive_checked_mail(self, *args):
        """Method to archive checked mails."""
        self.sudo().search([('id', 'in', *args),
                            ('create_uid', '=', self.env.user.id)]). \
            write({"active": False})

    @api.model
    def sent_mail(self, **kwargs):
        """Method to compose and send mail."""
        attachment_ids = []
        mail_from = self.env.user.email
        subject = kwargs.get('subject')
        recipient = kwargs.get('recipient')
        if not re.match(r"[^@]+@gmail\.com", recipient):
            raise ValidationError("Recipient email should be a Gmail address.")
        content = kwargs.get('content')
        content_html = content.replace('\n', '<br>')
        image = kwargs.get('images')
        if image:
            for img_data in image:
                image_data = img_data.get('image_uri')
                if image_data:
                    attachment = self.env['ir.attachment'].create({
                        'name': img_data.get('name'),
                        'datas': image_data,
                        'res_model': 'mail.mail',
                    })
                    attachment_ids.append((4, attachment.id))

        mail_id = self.sudo().with_user(user=self.env.user).create({
            "subject": subject,
            "email_to": recipient,
            "email_from": mail_from,
            "body_html": content_html,
            "attachment_ids": attachment_ids
        })

        mail_id.send()
        return mail_id.read()

    @api.model
    def retry_mail(self, *args):
        """Method to retry failed messages"""
        mail = self.search([('id', '=', int(*args)),
                            ('create_uid', '=', self.env.user.id)])
        mail.mark_outgoing()
        mail.send()
