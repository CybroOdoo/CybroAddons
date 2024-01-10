# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Amaya Aravind (odoo@cybrosys.com)
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
###############################################################################
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class PosOrderQuestion(models.Model):
    """Class for the model pos_order_question."""
    _name = 'pos.order.question'
    _description = 'POS Order Question'

    name = fields.Char(string='Questions', help='Questions for the product.')
    product_tmplt_id = fields.Many2one('product.template', string='Product',
                                       help='product template of the '
                                            'question.')

    @api.constrains('name')
    def _check_name(self):
        """Function to prevent saving empty questions."""
        for rec in self:
            if not rec.name:
                raise ValidationError(
                    _('Question cannot be empty.'))
