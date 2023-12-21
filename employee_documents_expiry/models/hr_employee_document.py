# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions (odoo@cybrosys.com)
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
###############################################################################
from datetime import datetime, date, timedelta

from odoo import api, fields, models, _


class HrEmployeeDocument(models.Model):
    """Create a new module for retrieving document files, allowing users
     to input details about the documents."""
    _name = 'hr.employee.document'
    _description = 'HR Employee Documents'

    name = fields.Char(string='Document Number', required=True, copy=False,
                       help="Enter Document Number")
    document_id = fields.Many2one('employee.checklist',
                                  string='Document',
                                  required=True,
                                  help="Choose Employee Checklist for"
                                       " Employee Document")
    description = fields.Text(string='Description', copy=False,
                              help="Description for Employee Document")
    expiry_date = fields.Date(string='Expiry Date', copy=False,
                              help="Choose Expiry Date for Employee Document")
    employee_id = fields.Many2one('hr.employee', copy=False, string="Employee",
                                  help="Choose Employee for Employee Document")
    doc_attachment_ids = fields.Many2many('ir.attachment',
                                          'doc_attach_ids',
                                          'doc_id', 'attach_id3',
                                          string="Attachment",
                                          help='You can attach the copy'
                                               'of your document',
                                          copy=False)
    issue_date = fields.Date(string='Issue Date',
                             default=fields.Date.context_today, copy=False,
                             help="Choose Issue Date for Employee Document")

    def mail_reminder(self):
        """Function for scheduling emails to send reminders
        about document expiry dates."""
        for doc in self.search([]):
            if doc.expiry_date:
                if (datetime.now() + timedelta(days=1)).date() >= (
                        doc.expiry_date - timedelta(days=7)):
                    mail_content = ("  Hello  " + str(
                        doc.employee_id.name) + ",<br>Your Document " + str(
                        doc.name) + "is going to expire on " + \
                                    str(doc.expiry_date) + ". Please renew it "
                                                           "before expiry date")
                    main_content = {
                        'subject': _('Document-%s Expired On %s') % (
                            str(doc.name), str(doc.expiry_date)),
                        'author_id': self.env.user.partner_id.id,
                        'body_html': mail_content,
                        'email_to': doc.employee_id.work_email,
                    }
                    self.env['mail.mail'].create(main_content).send()

    @api.onchange('expiry_date')
    def check_expr_date(self):
        """Function to obtain a validation error for expired documents."""
        if self.expiry_date and self.expiry_date < date.today():
            return {
                'warning': {
                    'title': _('Document Expired.'),
                    'message': _("Your Document Is Already Expired.")
                }
            }
