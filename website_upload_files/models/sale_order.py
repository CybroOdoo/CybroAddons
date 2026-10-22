# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#############################################################################
from odoo import fields, models


class SaleOrder(models.Model):
    """For adding the count of attachment as field in sale order"""
    _inherit = 'sale.order'

    attachment_count = fields.Integer(string='Uploaded File Count',
                                      help="Count of attachment",
                                      compute='_compute_attachment_count')

    def _compute_attachment_count(self):
        """Count the attachments of all orders in one query"""
        counts = dict(self.env['ir.attachment']._read_group(
            [('res_model', '=', 'sale.order'), ('res_id', 'in', self.ids)],
            ['res_id'], ['__count']))
        for order in self:
            order.attachment_count = counts.get(order.id, 0)

    def action_show_attachments(self):
        """To show attached documents"""
        self.ensure_one()
        return {
            'name': self.env._('Attachments'),
            'view_mode': 'kanban,form',
            'res_model': 'ir.attachment',
            'type': 'ir.actions.act_window',
            'domain': [('res_model', '=', 'sale.order'),
                       ('res_id', '=', self.id)]
        }
