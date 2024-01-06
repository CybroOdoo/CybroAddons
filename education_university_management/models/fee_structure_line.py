# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Raneesha M K (odoo@cybrosys.com)
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
from odoo import api, fields, models


class FeeStructureLines(models.Model):
    _name = 'fee.structure.line'
    _description = "Fee Structure lines"

    fee_structure_id = fields.Many2one('fee.structure',
                                       help="Relation to fee.structure",
                                       string='Fee Structure',
                                       ondelete='cascade', index=True)
    category_id = fields.Many2one(related='fee_structure_id.category_id',
                                  string="Category",
                                  help="Fee category of structure")
    fee_type_id = fields.Many2one('fee.type', string='Fee',
                                  required=True, help="Select fee types")
    currency_id = fields.Many2one('res.currency', string="Currency",
                                  default=lambda
                                      self: self.env.user.company_id.currency_id.id,
                                  help="Currency of current company")
    fee_amount = fields.Float('Amount', required=True,
                              help="Amount of the each fee type",
                              related='fee_type_id.lst_price')
    payment_type = fields.Selection(string='Payment Type',
                                    help="Payment type of fee type",
                                    related="fee_type_id.payment_type")
    fee_description = fields.Text('Description', help="Fee type "
                                                      "description",
                                  related='fee_type_id.description_sale')
