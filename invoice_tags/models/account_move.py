# -*- coding: utf-8 -*-
###################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    This program is free software: you can modify
#    it under the terms of the GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) as
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
###################################################################################
from odoo import api, fields, models


class AccountMove(models.Model):
    """Add field for tags in account.move"""
    _inherit = 'account.move'

    invoice_tag_ids = fields.Many2many('invoice.tag', string="Tags", help="Field for adding tags in invoice")

    @api.onchange('invoice_tag_ids')
    def _onchange_tag_filter(self):
        """Create filtering option in accordance with tags that are created"""
        created_tags = [tag for tag in self.invoice_tag_ids.search([])]
        linked_tags = [tag for tag in self.search([('id', '!=', self._origin.id)]).invoice_tag_ids]
        for result in self.invoice_tag_ids._origin:
            if result not in linked_tags:
                linked_tags.append(result)
            result.tag_filter_id.active = True
        for tags in created_tags:
            if tags not in linked_tags:
                tags.tag_filter_id.active = False
