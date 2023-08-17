# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Unnimaya C O (odoo@cybrosys.com)
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

from odoo import models, api, SUPERUSER_ID, _
from collections import defaultdict

from odoo.tools import float_compare


class MrpProductionInherit(models.Model):
    _inherit = 'stock.rule'

    @api.model
    def _run_manufacture(self, procurements):
        sale = []
        productions_values_by_company = defaultdict(list)
        for procurement, rule in procurements:
            if float_compare(procurement.product_qty, 0,
                             precision_rounding=procurement.product_uom.rounding) <= 0:
                # If procurement contains negative quantity, don't create a MO that would be for a negative value.
                continue
            current_sale_order = self.env['sale.order'].search(
                [('name', '=', procurement.origin)])
            if current_sale_order not in sale:
                sale.append(current_sale_order)
        bom_values = self._find_bom_order_line(sale)
        bom_exist = {key: value for key, value in bom_values.items() if value}
        if bom_exist:
            i = 0
            only_bom_record = list(bom_exist.keys())
            for procurement, rule in procurements:
                productions_values_by_company[procurement.company_id.id].append(rule._prepare_mo_vals(*procurement, bom_exist[only_bom_record[i]]))
                i = i + 1
        for company_id, productions_values in productions_values_by_company.items():
            # create the MO as SUPERUSER because the current user may not have the rights to do it (mto product launched by a sale for example)
            productions = self.env['mrp.production'].with_user(
                SUPERUSER_ID).sudo().with_company(company_id).create(
                productions_values)
            productions.filtered(
                self._should_auto_confirm_procurement_mo).action_confirm()
            for production in productions:
                origin_production = production.move_dest_ids and \
                                    production.move_dest_ids[
                                        0].raw_material_production_id or False
                orderpoint = production.orderpoint_id
                if orderpoint and orderpoint.create_uid.id == SUPERUSER_ID and orderpoint.trigger == 'manual':
                    production.message_post(
                        body=_(
                            'This production order has been created from Replenishment Report.'),
                        message_type='comment',
                        subtype_xmlid='mail.mt_note')
                elif orderpoint:
                    production.message_post_with_view(
                        'mail.message_origin_link',
                        values={'self': production, 'origin': orderpoint},
                        subtype_id=self.env.ref('mail.mt_note').id)
                elif origin_production:
                    production.message_post_with_view(
                        'mail.message_origin_link',
                        values={'self': production,
                                'origin': origin_production},
                        subtype_id=self.env.ref('mail.mt_note').id)
        return True

    def _find_bom_order_line(self, sale):
        bom_list = {}
        j = 1
        for rec in sale[0].order_line:
            if rec.bom_id:
                bom_list.update({j: rec.bom_id })
            elif rec.product_template_id.route_ids:
                bom = self.env['mrp.bom'].search([("product_tmpl_id","=",rec.product_template_id.id)], limit=1)
                bom_list.update({j:bom })
            j = j + 1
        return bom_list
