# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Cybrosys Technologies (<https://www.cybrosys.com>)
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
from odoo import models


class ResPartner(models.Model):
    """res.partner is inherited."""
    _inherit = 'res.partner'

    def action_view_sale_order(self):
        """This is to add a new pivot view to customer to show
        their sale orders."""
        action = self.env['ir.actions.act_window']._for_xml_id(
            'sale.act_res_partner_2_sale_order')
        all_child = self.with_context(active_test=False).search(
            [('id', 'child_of', self.ids)])
        action["domain"] = [("partner_id", "in", all_child.ids)]
        action["view_mode"] = "tree,kanban,form,graph,pivot"
        action["views"] = [(False, 'tree'), (False, 'kanban'),
                           (False, 'form'), (False, 'graph'), (False, 'pivot')]
        return action
