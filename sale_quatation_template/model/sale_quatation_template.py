# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2020-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: YADHU K (odoo@cybrosys.com)
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
from odoo import fields, models, api
from odoo.exceptions import ValidationError
from odoo.tools.translate import _


class WizardCreateTemplate(models.Model):
    _inherit = 'sale.order'

    def create_template(self):
        order_line_ids = []
        option_line_ids = []
        Template = self.env['sale.order.template']
        name = 'QT/' + self.partner_id.name
        if self.order_line:
            quot_template = Template.create({
                'name': name,
            })
            for line in self.order_line:
                order_line_ids.append((0, 0, {
                    'product_id': line.product_id.id,
                    'name': line.name,
                    'product_uom_qty': line.product_uom_qty,
                    'product_uom_id': line.product_id.product_tmpl_id.uom_id.id,
                    'price_unit': line.price_unit,
                }))

            for line in self.sale_order_option_ids:
                option_line_ids.append((0, 0, {
                    'product_id': line.product_id.id,
                    'name': line.name,
                    'quantity': line.quantity,
                    'uom_id': line.product_id.product_tmpl_id.uom_id.id,
                    'price_unit': line.price_unit,
                }))

            quot_template.update({
                'sale_order_template_line_ids': order_line_ids,
                'sale_order_template_option_ids': option_line_ids,
            })
            if quot_template:
                self.sale_order_template_id = quot_template.id
        else:
            raise ValidationError(_("Sale order has no order lines"))


