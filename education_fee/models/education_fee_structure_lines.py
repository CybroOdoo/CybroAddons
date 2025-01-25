# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Gayathri V (odoo@cybrosys.com)
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
from odoo import api, fields, models


class EducationFeeStructureLines(models.Model):
    """Creating model 'education.fee.structure.lines'"""
    _name = 'education.fee.structure.lines'
    _description = 'Education Fee Structure Lines'

    @api.onchange('fee_type_id')
    def _onchange_fee_type(self):
        """Function to return Fee type ids"""
        return {
            'domain': {
                'fee_type_id': [('category_id', '=',
                                 self.fee_structure_id.category_id.id)]
            }
        }

    fee_type_id = fields.Many2one('education.fee.type', string='Fee',
                                  required=True,
                                  help='Fee Type of fee structure')
    fee_structure_id = fields.Many2one('education.fee.structure',
                                       string='Fee Structure',
                                       ondelete='cascade', index=True,
                                       help='Education fee structure of lines')
    fee_amount = fields.Float('Amount', required=True,
                              related='fee_type_id.lst_price',
                              help='Corresponding fee amount.')
    payment_type = fields.Selection([
        ('onetime', 'One Time'),
        ('permonth', 'Per Month'),
        ('peryear', 'Per Year'),
        ('sixmonth', '6 Months'),
        ('threemonth', '3 Months')
    ], string='Payment Type', related="fee_type_id.payment_type",
        help='Payment type describe how much a payment effective Like,'
             ' bus fee per month is 30 dollar, sports fee per year'
             ' is 40 dollar, etc')
    interval = fields.Char(related="fee_type_id.interval", string="Interval",
                           help='Specify the interval.')
    fee_description = fields.Text('Description',
                                  related='fee_type_id.description_sale',
                                  help='Give the fee description.')
