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
from odoo import Command, models



class ProductTemplate(models.Model):
    """ Inheriting product template to add fields for publish
        product in website """
    _inherit = 'product.template'

    def quick_publish_products(self):
        """ Function for publish product in website shop """
        for rec in self:
            rec.is_published = True if not rec.is_published else False
        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
        }

    def action_published(self):
        """Function on button to publish the product"""
        self.is_published = True

    def action_unpublished(self):
        """Function on button to un publish the product"""
        self.is_published = False

    def action_publish(self):
        return {
            'name': "Publish/Unpublish Products",
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'product.publish',
            'view_id': self.env.ref(
                'website_product_publish.product_publish_view_form').id,
            'target': 'new',
            'context': {
                'default_product_ids': [Command.set(self.ids)],
            },
        }
