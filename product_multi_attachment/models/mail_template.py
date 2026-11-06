# -*- coding: utf-8 -*-
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
from odoo import models


class MailTemplate(models.Model):
    """Inherits mail.template to include product attachments from order lines."""

    _inherit = 'mail.template'

    def _generate_template_attachments(
        self, res_ids, render_fields, render_results=None,
    ):
        """Override to add product attachments from order lines into email."""
        res = super()._generate_template_attachments(
            res_ids, render_fields, render_results,
        )
        target_model = self.render_model or self.model
        if target_model == 'purchase.order':
            for res_id in res_ids:
                order = self.env['purchase.order'].browse(res_id)
                attachment_ids = order.order_line.mapped(
                    'attachment_ids',
                ).ids
                if attachment_ids:
                    existing = res.setdefault(res_id, {}).get(
                        'attachment_ids', [],
                    )
                    res[res_id]['attachment_ids'] = list(
                        set(existing + attachment_ids),
                    )
        elif target_model == 'sale.order':
            for res_id in res_ids:
                order = self.env['sale.order'].browse(res_id)
                attachment_ids = order.order_line.mapped(
                    'attachment_ids',
                ).ids
                if attachment_ids:
                    existing = res.setdefault(res_id, {}).get(
                        'attachment_ids', [],
                    )
                    res[res_id]['attachment_ids'] = list(
                        set(existing + attachment_ids),
                    )
        return res
