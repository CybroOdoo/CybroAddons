# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Gayathri V (odoo@cybrosys.com)
#
#    This program is free software: you can modify
#    it under the terms of the GNU LESSER GENERAL PUBLIC LICENSE (LGPL) as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
###############################################################################
from odoo import api, fields, models


class PartnerDocuments(models.Model):
    """This class Inherits the res.partner model to add document count field"""
    _inherit = 'res.partner'

    document_count = fields.Char(compute='_compute_total_document_count',
                                 string='Document Count',
                                 help='Get the documents count')

    @api.depends('document_count')
    def _compute_total_document_count(self):
        """Get the document count on smart tab"""
        for record in self:
            record.document_count = self.env[
                'ir.attachment'].search_count(
                [('res_id', '=', self.id), ('res_model', '=', 'res.partner')])

    def action_partner_documents(self):
        """Return the documents of corresponding partner in the smart tab"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Documents',
            'view_mode': 'kanban,form',
            'res_model': 'ir.attachment',
            'domain': [('res_id', '=', self.id),
                       ('res_model', '=', 'res.partner')],
            'context': "{'create': True}"
        }
