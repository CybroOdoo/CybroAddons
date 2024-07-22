# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Sreeshanth V S(<https://www.cybrosys.com>)
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
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
from odoo import fields, models


class DocumentReject(models.TransientModel):
    """ Wizard for rejecting documents"""
    _name = "document.reject"
    _description = "Wizard for document reject"
    _rec_name = "document_id"

    description = fields.Text(string="Description",
                              help='For adding reason for the rejection')
    document_id = fields.Many2one("document.approval", string="Document",
                                  help="To track which document is get approved"
                                  )

    def action_reject_document(self):
        """ Function to reject document"""
        self.document_id.state = "reject"
        for rec in self.document_id.step_ids.filtered(
                lambda x: x.approver_id.id == self.env.user.id):
            rec.write({
                'current_state': 'rejected',
            })
