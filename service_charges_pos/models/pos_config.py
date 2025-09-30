# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2025-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions(odoo@cybrosys.com)
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
from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.osv.expression import OR


class PosConfig(models.Model):
    """
    To inherit model pos.config
    """
    _inherit = 'pos.config'

    is_service_charges = fields.Boolean("Service Charges", help="Enable Service Charges")
    visibility_type = fields.Selection([
        ('global', 'Global'),
        ('session', 'Session')],
        string='Visibility', default='global',
        help="Can choose visibility of service charges.")
    service_charge = fields.Float(string='Service Charge',
                                  help="Charge need to apply",
                                  default=10.0)
    service_product_id = fields.Many2one('product.product',
                                         string='Service Product',
                                         domain="[('sale_ok', '=', True)]",
                                         help="Service Product")
    service_charge_type = fields.Selection([
        ('amount', 'Amount'),
        ('percentage', 'Percentage')],
        string='Type', default='amount',
        help="Can choose charge percentage or amount")

    @api.model
    def _default_service_charge_on_module_install(self):
        """
        Set default service product on module installation"""
        configs = self.env['pos.config'].search([])
        open_configs = (
            self.env['pos.session']
            .search(['|', ('state', '!=', 'closed'), ('rescue', '=', True)])
            .mapped('config_id')
        )
        # Do not modify configs where an opened session exists.
        product = self.env.ref("point_of_sale.product_product_consumable",
                               raise_if_not_found=False)
        for conf in (configs - open_configs):
            conf.service_product_id = product if (
                 conf.is_service_charges
            ) and product and (
                not product.company_id or product.company_id == conf.company_id
            ) else False

    def open_ui(self):
        """
        Overridden to check if service product is set when service charge is enabled"""
        for config in self:
            if not self.current_session_id and (
                    config.is_service_charges
            ) and not config.service_product_id:
                raise UserError(_(
                    'A discount product is needed to use the Service Charge '
                    'feature. Go to Point of Sale > Configuration > Settings '
                    'to set it.'))
        return super().open_ui()

    def _get_special_products(self):
        """ Overridden to add service product to the list of special products"""
        res = super()._get_special_products()
        return res | self.env['pos.config'].search(
            []).mapped('service_product_id')

    def _get_available_product_domain(self):
        """ Overridden to include service product in the available products"""
        domain = super()._get_available_product_domain()
        return OR([domain, [('id', '=', self.service_product_id.id)]])
