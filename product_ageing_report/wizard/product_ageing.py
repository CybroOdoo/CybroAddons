# -*- coding: utf-8 -*-
##############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2017-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Linto C T(<https://www.cybrosys.com>)
#    you can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.

#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    GENERAL PUBLIC LICENSE (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from odoo import models, fields, api


class AgeingAnalysis(models.Model):
    _name = 'product.ageing'

    from_date = fields.Datetime(string="Starting Date", required=True)
    location_id = fields.Many2many('stock.location', string="Location")
    product_categ = fields.Many2many('product.category', string="Category")
    interval = fields.Integer(string="Interval(days)", default=30, required=True)

    @api.model
    def compute_ageing(self, data):
        """Redirects to the report with the values obtained from the wizard
                'data['form']':  date duration"""
        rec = self.browse(data)
        data = {}
        data['form'] = rec.read(['from_date', 'location_id', 'product_categ', 'interval'])
        return self.env['report'].get_action(rec, 'product_ageing_report.report_ageing_analysis',
                                             data=data)

