# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: odoo@cybrosys.com
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


from odoo import fields, models


class ResPartner(models.Model):
    """
        This class inherited to add some extra fields and functions in the
        Partner
    """
    _inherit = 'res.partner'

    customer_supplier_id = fields.Char(string="ID",
                                       domain="[('state', '=', 'validated')]",
                                       help="Unique id for partners")
    hide_button = fields.Boolean(default=False,
                                 help="This boolean field is used to hide the approve button")
    hide_button_validate = fields.Boolean(default=False,
                                          help="This boolean field is used to hide the Validate button")
    state = fields.Selection([
        ('draft', 'Draft'),
        ('validated', 'Validated'),
        ('approved', 'Approved'),
    ], default='draft', help="The states are in Draft,Validated and Approved")
    _sql_constraints = [
        ('id_uniq', 'unique (customer_supplier_id)', 'The partner id unique !')
    ]

    def action_validate(self):
        """
            customer or supplier can validate
        """
        for rec in self:
            rec.hide_button_validate = True
            rec.write({'state': 'validated'})

    def action_approve(self):
        """
            customer or supplier can Approve
        """
        for rec in self:
            rec.state = 'validated'
            rec.hide_button = True
            rec.write({'state': 'approved'})
