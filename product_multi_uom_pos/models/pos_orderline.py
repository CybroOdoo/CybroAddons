# -*- coding: utf-8 -*-

##############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2018-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: LINTO C T(<https://www.cybrosys.com>)
#    you can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    GENERAL PUBLIC LICENSE (LGPL v3) along with this program.
#    If not, see <https://www.gnu.org/licenses/>.
#
##############################################################################
from odoo import _
from odoo.tools import float_is_zero
from odoo import models, fields, api
from itertools import groupby


class PosOrderLinesExtended(models.Model):
    _inherit = 'pos.order.line'

    uom_id = fields.Many2one('uom.uom', string="UOM")

    @api.model
    def create(self, values):

        if values.get('uom_id'):
            values['uom_id'] = values['uom_id'][0]
        else:
            values['uom_id'] = None
        res = super(PosOrderLinesExtended, self).create(values)
        return res
