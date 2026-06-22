# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies (<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions (<https://www.cybrosys.com>)
#
#    This program is free software: you can modify it under the terms of the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful, but
#    WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################

from odoo import models,_


class ProductProduct(models.Model):
    """This class extends the 'product.product' model to add functionality for importing images via a wizard."""
    _inherit = 'product.product'

    def action_open_import_image_wizard(self):
        """Opens the 'Import Image' wizard form view."""
        return {
            'type': 'ir.actions.act_window',
            'name': _('Import Image'),
            'res_model': 'import.image',
            'views': [[False, 'form']],
            'target': 'new',
            'context':{
                'default_parent_model':self._name,
                'default_model_template':self._name,
                'parent_model': self._name,
            }
        }
