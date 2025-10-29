# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2025-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
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
from odoo import api, fields, models
from odoo.osv import expression
from odoo.tools import Query


class ProductTemplate(models.Model):
    """Inherited product template for adding the field Hot Sale and Product
    Brand. While using the snippet  'Product Tab', the product with enabled
    Hot Sale will be display."""
    _inherit = "product.template"

    hot_deals = fields.Boolean(string="Hot Sale", help='The product or services'
                                                       'which are high in'
                                                       'demand at a particular'
                                                       'time or period')
    brand_id = fields.Many2one('product.brand', string="Product Brand",
                               help='Enabled product can filter from website'
                                    'by brand.')

    def _search_get_detail(self, website, order, options):
        res = super()._search_get_detail(website, order, options)
        if options.get('brand_ids', None):
            res['base_domain'].append(
                [('brand_id.id', 'in', options['brand_ids'])])
        return res

    @api.model
    def _where_calc(self, domain, active_test=True):
        """Computes the WHERE clause needed to implement an OpenERP domain.

        :param list domain: the domain to compute
        :param bool active_test: whether the default filtering of records with
            ``active`` field set to ``False`` should be applied.
        :return: the query expressing the given domain as provided in domain
        :rtype: Query
        """
        # if the object has an active field ('active', 'x_active'), filter out all
        # inactive records unless they were explicitly asked for
        if self._active_name and active_test and self._context.get('active_test', True):
            # the item[0] trick below works for domain items and '&'/'|'/'!'
            # operators too
            if not any(item[0] == self._active_name for item in domain):
                domain = [(self._active_name, '=', 1)] + domain

        if domain:
            return expression.expression(domain, self).query
        else:
            return Query(self.env, self._table, self._table_sql)
