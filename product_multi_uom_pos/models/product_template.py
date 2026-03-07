# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Anjali VP (Contact : odoo@cybrosys.com)
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
from odoo import fields, models, api

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    multi_uom = fields.Boolean(
        compute='_compute_multi_uom',
        string='Multi UoM',
        help='A boolean field to show the one2many field POS Multiple UoM'
    )

    pos_multi_uom_ids = fields.One2many(
        'pos.multi.uom',
        'product_template_id',
        string="POS Multiple UoM"
    )

    @api.depends_context('company')
    def _compute_multi_uom(self):
        """Computes the status of multi uom from the system parameters."""
        # Reading system parameter
        param = self.env['ir.config_parameter'].sudo().get_param('product_multi_uom_pos.pos_multi_uom')
        status = bool(param)

        for record in self:
            record.multi_uom = status


    @api.model
    def _load_pos_data_domain(self, data):
        """Define the domain for records to load in POS"""
        return []

    @api.model
    def _load_pos_data_search_read(self, data, config):
        """Search and return records to be loaded in the pos"""
        fields = self._load_pos_data_fields(config.id)
        domain = self._load_pos_data_domain(data)
        return self.search_read(domain, fields)


