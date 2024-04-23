# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions (Contact : odoo@cybrosys.com)
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
################################################################################
from odoo import api, fields, models, _


class SaleOrder(models.Model):
    """This class inherits the model sale order for adding fields and functions
     for versioning."""
    _inherit = "sale.order"

    is_version = fields.Boolean(string="Is Version",
                                help="For checking version or not")

    version_count = fields.Integer(string="Sale Version Count",
                                   compute='_compute_version_ids',
                                   help="Count of version created")
    current_version_id = fields.Many2one("sale.order",
                                         help="For creating versions")
    version_ids = fields.One2many("sale.order",
                                  inverse_name="current_version_id",
                                  help="Versions created")

    def action_create_versions(self):
        """For creating the versions of the sale order"""
        sale_order_copy_id = self.copy()
        sale_order_copy_id.is_version = True
        length = len(self.version_ids)
        sale_order_copy_id.name = "%s-%s" % (self.name, str(length + 1))
        order_lines = []
        val = (0, 0, {
            'display_type': 'line_note',
            'name': 'This is version %s ' %(str(length + 1)),
            'product_id': False,
            'product_uom_qty': 0,
            'product_uom': False,
            'price_unit': 0,
            'order_id': sale_order_copy_id.id,
            'tax_id': False,
        })
        order_lines.append(val)
        sale_order_copy_id.update({'order_line': order_lines})

        self.write({'version_ids': [(4, sale_order_copy_id.id)]})

    @api.depends('version_ids')
    def _compute_version_ids(self):
        """For calculating the number of versions created"""
        for sale in self:
            sale.version_count = len(sale.version_ids)

    def action_view_versions(self):
        """action for viewing versions"""
        action = {
            "type": "ir.actions.act_window",
            "view_mode": "kanban,tree,form",
            "name": _("Sale Order Versions"),
            "res_model": self._name,
            "domain": [('id', 'in', self.version_ids.ids)],
            "target": "current",
        }
        return action

    def action_confirm(self):
        """Override the confirm button of the sale order for cancelling the
        other versions and making the current version main"""
        res = super().action_confirm()
        if not self.version_ids:
            parent_sale = self.current_version_id
            versions = parent_sale.mapped('version_ids').mapped('id')
            if versions:
                versions.append(parent_sale.id)
            for version in parent_sale.version_ids:
                if version.state == 'sale':
                    # Updating the version name into main version name and
                    # other versions state into cancel
                    version.current_version_id.update({'is_version': True,
                                                       'state': 'cancel'})
                    version.update({'version_ids': versions,
                                    "name": version.current_version_id.name,
                                    'is_version': False})
                if version.state == 'draft':
                    version.update({'state': 'cancel'})
        else:
            if self.state == 'sale':
                for sale in self.version_ids:
                    sale.update({'state': 'cancel'})
        return res
