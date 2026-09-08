# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions (odoo@cybrosys.com)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <https://www.gnu.org/licenses/>.
#
#############################################################################
import datetime

from odoo import api, fields, models, _


class ComplianceDocument(models.Model):
    """Secure repository for environmental permits, facility licences, and compliance certificates."""
    _name = 'wm.compliance.document'
    _description = 'Compliance Document Vault'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'expiry_date asc, id desc'

    name = fields.Char(string='Document Name', required=True)

    document_type = fields.Selection([
        ('permit', 'Permit'),
        ('licence', 'Licence'),
        ('certificate', 'Certificate'),
        ('authorization', 'Authorization'),
        ('other', 'Other')
    ], string='Document Type', required=True, default='permit')

    attachment_id = fields.Many2one('ir.attachment', string='Attachment Record', ondelete='cascade')

    attachment_file = fields.Binary(
        string='Attachment File',
        compute='_compute_attachment_file',
        inverse='_inverse_attachment_file',
        required=True,
        store=False
    )
    attachment_filename = fields.Char(
        string='Attachment Filename',
        compute='_compute_attachment_file',
        inverse='_inverse_attachment_file',
        store=False
    )

    expiry_date = fields.Date(string='Expiry Date', required=True)
    reminder_days = fields.Integer(string='Reminder Days', default=30, required=True)
    user_id = fields.Many2one(
        'res.users',
        string='Responsible User',
        default=lambda self: self.env.user,
        required=True
    )

    company_id = fields.Many2one(
        'res.company',
        string='Company',
        required=True,
        default=lambda self: self.env.company
    )

    @api.depends('attachment_id')
    def _compute_attachment_file(self):
        """
        Retrieve the most recently uploaded file attachment for this vault
        document, exposing it as a binary field for direct download from the
        permit vault form.
        """
        for rec in self:
            if rec.attachment_id:
                rec.attachment_file = rec.attachment_id.datas
                rec.attachment_filename = rec.attachment_id.name
            else:
                rec.attachment_file = False
                rec.attachment_filename = False

    def _inverse_attachment_file(self):
        """
        Handle direct binary uploads to the vault document by creating or
        replacing the underlying ir.attachment record and linking it to this
        permit vault entry.
        """
        for rec in self:
            if rec.attachment_file:
                if rec.attachment_id:
                    rec.attachment_id.write({
                        'datas': rec.attachment_file,
                        'name': rec.attachment_filename or 'document',
                    })
                else:
                    attachment = self.env['ir.attachment'].create({
                        'name': rec.attachment_filename or 'document',
                        'datas': rec.attachment_file,
                        'res_model': 'wm.compliance.document',
                        'res_id': rec.id,
                    })
                    rec.attachment_id = attachment
            else:
                if rec.attachment_id:
                    rec.attachment_id = False

    @api.model
    def cron_check_document_expiry(self):
        """
        Scheduled cron job action for check document expiry.
        """
        today = fields.Date.today()
        # Find all documents
        docs = self.search([('expiry_date', '!=', False)])

        # Odoo 19: Get the "To Do" activity type
        todo_activity_type = self.env.ref('mail.mail_activity_data_todo', raise_if_not_found=False)
        if not todo_activity_type:
            # Fallback if the standard XML ID is not present
            todo_activity_type = self.env['mail.activity.type'].search([('category', '=', 'default')], limit=1)

        if not todo_activity_type:
            return

        for doc in docs:
            expiry_date = fields.Date.from_string(doc.expiry_date)
            reminder_date = expiry_date - datetime.timedelta(days=doc.reminder_days)
            if reminder_date <= today:
                # Find responsible user
                responsible_user_id = doc.user_id.id or self.env.user.id

                # Check if activity already exists to avoid spamming
                existing = self.env['mail.activity'].search([
                    ('res_model', '=', 'wm.compliance.document'),
                    ('res_id', '=', doc.id),
                    ('activity_type_id', '=', todo_activity_type.id),
                    ('user_id', '=', responsible_user_id),
                ])
                if not existing:
                    self.env['mail.activity'].create({
                        'res_model_id': self.env['ir.model']._get_id('wm.compliance.document'),
                        'res_id': doc.id,
                        'activity_type_id': todo_activity_type.id,
                        'summary': _("Document Expiry: %s") % doc.name,
                        'note': _("The compliance document '%s' will expire on %s. Please review and renew.") % (doc.name, doc.expiry_date),
                        'date_deadline': doc.expiry_date,
                        'user_id': responsible_user_id,
                    })
