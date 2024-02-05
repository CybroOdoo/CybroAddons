# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Gayathti V (odoo@cybrosys.com)
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
from odoo import fields, models, _


class SaleOrder(models.Model):
    """For adding the count of attachment as field in sale order"""
    _inherit = 'sale.order'

    attachment_count = fields.Integer(string='Attachment Count',
                                      help="Count of attachment",
                                      compute='_compute_attachment_count')

    def _compute_attachment_count(self):
        """Count of attached documents"""
        for rec in self:
            rec.attachment_count = self.env['ir.attachment'].search_count(
                [('res_model', '=', 'sale.order'), ('res_id', '=', rec.id)])

    def action_show_attachments(self):
        """To show attached documents"""
        return {
            'name': _('Attachments'),
            'view_mode': 'kanban,form',
            'res_model': 'ir.attachment',
            'type': 'ir.actions.act_window',
            'domain': [('res_model', '=', 'sale.order'),
                       ('res_id', '=', self.id)]
        }
