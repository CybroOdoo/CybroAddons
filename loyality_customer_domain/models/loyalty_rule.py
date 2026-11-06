#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#############################################################################
import ast

from odoo import api, fields, models
from odoo.exceptions import ValidationError
from odoo.fields import Domain


class LoyaltyRule(models.Model):
    """Restrict the loyalty rules to the customers of a domain."""
    _inherit = 'loyalty.rule'

    customer_domain = fields.Char(
        default="[]",
        help="The rule only applies to the orders of the customers matching "
             "this domain")

    @api.constrains('customer_domain')
    def _check_customer_domain(self):
        """The customer domain must be a valid domain on the contacts, with
        fixed values only, since it is checked on every order."""
        for rule in self:
            try:
                domain = rule._get_customer_domain()
                self.env['res.partner'].sudo().search_count(domain, limit=1)
            except Exception as error:  # pylint: disable=broad-exception-caught
                raise ValidationError(self.env._(
                    "The customer domain of the rule is not valid: %(error)s",
                    error=error)) from error

    def _get_customer_domain(self):
        """Return the customer domain of the rule."""
        self.ensure_one()
        if self.customer_domain and self.customer_domain != '[]':
            return Domain(ast.literal_eval(self.customer_domain))
        return Domain.TRUE

    def _is_customer_eligible(self, partner):
        """Return whether the rule applies to the orders of the partner."""
        self.ensure_one()
        domain = self._get_customer_domain()
        if domain.is_true():
            return True
        return bool(partner) and bool(
            self.env['res.partner'].sudo().with_context(active_test=False)
            .search_count(Domain('id', '=', partner.id) & domain, limit=1))

    def _get_valid_product_domain(self):
        """While the points of an order are computed, a rule whose customer
        domain excludes the customer of the order matches no product, so
        that the order skips the rule."""
        domain = super()._get_valid_product_domain()
        if 'loyalty_customer_id' in self.env.context:
            partner = self.env['res.partner'].browse(
                self.env.context['loyalty_customer_id'])
            if not self._is_customer_eligible(partner):
                return Domain.FALSE
        return domain
