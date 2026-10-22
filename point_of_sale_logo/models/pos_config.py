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
from odoo import fields, models
from odoo.tools.image import image_data_uri


class PosConfig(models.Model):
    """Inherited pos config for uploading logo image"""
    _inherit = 'pos.config'

    image = fields.Binary(help="Set logo image for viewing it in POS Screen and Receipt")
    logo_option = fields.Selection(
        selection=[
            ('pos', 'Show POS Logo Only'),
            ('company', 'Show Company Logo Only'),
            ('both', 'Show Both POS and Company Logos')],
        string="Receipt Logo Option",
        default='pos',
        help="Choose which logo(s) to display on the printed POS receipt.")


class PosOrderReceipt(models.AbstractModel):
    """Inherited pos.order.receipt to pass custom logo options for receipt generation"""
    _inherit = 'pos.order.receipt'

    def order_receipt_generate_data(self, basic_receipt=False):
        """Generate POS order receipt data with the selected logo option.

           Supports displaying the POS logo, company logo, or both logos
           on the order receipt based on the POS configuration.
           """
        res = super().order_receipt_generate_data(basic_receipt=basic_receipt)
        config = self.config_id

        pos_logo = image_data_uri(config.image) if config.image else False
        company_logo = (
            image_data_uri(self.company_id.logo)
            if self.company_id.logo
            else res.get('image', {}).get('logo')
        )

        logo_option = config.logo_option or 'pos'
        image_data = res.setdefault('image', {})
        image_data['logo_option'] = logo_option

        if logo_option == 'pos':
            image_data['logo'] = pos_logo or company_logo
            image_data['pos_logo'] = False
            image_data['company_logo'] = False
        elif logo_option == 'company':
            image_data['logo'] = company_logo
            image_data['pos_logo'] = False
            image_data['company_logo'] = False
        elif logo_option == 'both':
            image_data['pos_logo'] = pos_logo
            image_data['company_logo'] = company_logo
            image_data['logo'] = False

        return res
