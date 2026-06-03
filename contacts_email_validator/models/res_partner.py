# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
###############################################################################

import logging
import re
import dns.resolver
from odoo import api, models
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)

class ResPartner(models.Model):
    _inherit = 'res.partner'

    @api.constrains('email')
    def _check_email_validate(self):
        """ Validate email format and check MX records if the setting is enabled. """

        # Check if validation is enabled in system settings
        validation_enabled = self.env['ir.config_parameter'].sudo().get_param(
            'contacts_email_validator.email_validation')
        if not validation_enabled or validation_enabled.lower() != 'true':
            return  # Skip validation if disabled

        email_regex = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'

        for record in self:
            if record.email:
                # Check if email format is valid
                if not re.match(email_regex, record.email):
                    raise ValidationError(f"Invalid email format: {record.email}")

                # Extract domain from email
                domain = record.email.split('@')[-1]

                try:
                    # Check MX records for the domain
                    mx_records = dns.resolver.resolve(domain, 'MX')
                    if not mx_records:
                        raise ValidationError(f"No valid mail server found for domain: {domain}")

                except dns.resolver.NoAnswer:
                    raise ValidationError(f"No mail server found for domain: {domain}")
                except dns.resolver.NXDOMAIN:
                    raise ValidationError(f"Invalid domain: {domain}")
                except dns.resolver.NoNameservers:
                    _logger.warning(f"No nameservers found for domain: {domain}")
                except dns.resolver.Timeout:
                    _logger.warning(f"DNS lookup timeout for domain: {domain}")
                except Exception as e:
                    _logger.error(f"DNS lookup error for domain {domain}: {str(e)}")
