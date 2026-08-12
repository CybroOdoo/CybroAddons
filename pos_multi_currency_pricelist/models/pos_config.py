# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions (odoo@cybrosys.com)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################
from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class PosConfig(models.Model):
    """Extend the POS configuration to support multi-currency pricelists."""
    _inherit = "pos.config"

    enable_multi_currency_pricelist = fields.Boolean(
        string="Multi-Currency Pricelists",
        help="Allow POS pricelists with different currencies and use the "
             "selected pricelist currency in the POS interface.",
    )

    @api.constrains(
        "pricelist_id",
        "use_pricelist",
        "available_pricelist_ids",
        "journal_id",
        "invoice_journal_id",
        "payment_method_ids",
        "enable_multi_currency_pricelist",
    )
    def _check_currencies(self):
        """Validate currency consistency for the POS configuration."""
        for config in self:
            if (config.use_pricelist and config.pricelist_id
                    and config.pricelist_id not in config.available_pricelist_ids):
                raise ValidationError(_("The default pricelist must be included "
                                        "in the available pricelists."))

            for payment_method in config.payment_method_ids:
                if (
                    payment_method.journal_id
                    and payment_method.journal_id.currency_id
                    and payment_method.journal_id.currency_id != config.currency_id
                ):
                    raise ValidationError(
                        _(
                            "All payment methods must be in the same currency "
                            "as the Sales Journal or the company currency if that"
                            " is not set."
                        )
                    )

            if (
                not config.enable_multi_currency_pricelist
                and config.use_pricelist
                and any(pricelist.currency_id != config.currency_id for
                        pricelist in config.available_pricelist_ids)
            ):
                raise ValidationError(
                    _(
                        "All available pricelists must be in the same currency "
                        "as the company or as the Sales Journal set on this point "
                        "of sale if you use the Accounting application."
                    )
                )

            if (config.invoice_journal_id.currency_id and
                    config.invoice_journal_id.currency_id != config.currency_id):
                raise ValidationError(
                    _("The invoice journal must be in the same currency as the "
                      "Sales Journal or the company currency if that is not set.")
                )
