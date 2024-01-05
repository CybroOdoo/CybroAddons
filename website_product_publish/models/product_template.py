# -*- coding: utf-8 -*-
###############################################################################
#
# Cybrosys Technologies Pvt. Ltd.
#
# Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
# Author: Jumana Haseen (odoo@cybrosys.com)
#
# You can modify it under the terms of the GNU AFFERO
# GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
# You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
# (AGPL v3) along with this program.
# If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################
from odoo import models


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
        """ Open a wizard for publish or un publish products
                 based on the selected products."""
        return {
            'name': "Publish/Unpublish products",
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'product.publish',
            'view_id': self.env.ref(
                'website_product_publish.product_publish_view_form').id,
            'target': 'new',
            'context': {
                'default_product_ids': self.env.context.get('active_ids')
            },
        }
