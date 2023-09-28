# -*- coding: utf-8 -*-
##############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Mohammed Irfan T (odoo@cybrosys.com)
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
##############################################################################
from odoo import api, fields, models, _


class SaleOrder(models.Model):
    """Inherits Sales to create sale order versions"""
    _inherit = "sale.order"

    is_version = fields.Boolean(string="Is Version",
                                help="For checking version or not")
    version_count = fields.Integer(string="Sale Version Count",
                                   compute='_compute_version_ids',
                                   help="Count of version created")
    current_version_id = fields.Many2one("sale.order",
                                         string='Current version',
                                         help="For creating versions")
    version_ids = fields.One2many("sale.order", string='Version',
                                  inverse_name="current_version_id",
                                  help="Versions created")
    state = fields.Selection(selection_add=[('revised', 'Revised')],
                             string='State', help='State of the sale order')

    def action_create_versions(self):
        """For creating the versions of the sale order."""
        sale_order_copy_id = self.copy()
        sale_order_copy_id.is_version = True
        length = len(self.version_ids)
        sale_order_copy_id.name = "%s-%s" % (self.name, str(length + 1))
        sale_order_copy_id.state = 'revised'
        self.write({'version_ids': [(4, sale_order_copy_id.id)]})

    @api.depends('version_ids')
    def _compute_version_ids(self):
        """For calculating the number of versions created."""
        for sale in self:
            sale.version_count = len(sale.version_ids)

    def action_view_versions(self):
        """Action for viewing versions"""
        action = {
            "type": "ir.actions.act_window",
            "view_mode": "kanban,tree,form",
            "name": _("Sale Order Versions"),
            "res_model": self._name,
            "domain": [('id', 'in', self.version_ids.ids)],
            "target": "current"
        }
        return action

    def action_restore(self):
        """
            Restore the current version of a sale and cancel all other versions
            This method restores the current version of a sale to the 'draft'
            state and cancels all other versions of the sale by setting their
            state to 'cancel'.
            :return: None
        """
        parent_sale = self.current_version_id
        self.write({'state': 'draft'})
        for version in parent_sale.version_ids:
            if version != self:
                version.write({'state': 'cancel'})

    def set_to_revise(self):
        """
            Set the state of the record to 'revised'.
            This method updates the state of the record to 'revised'. It is
            typically used to indicate that the record has undergone a revision
            or modification.
            :return: None
        """
        self.write({'state': 'revised'})
