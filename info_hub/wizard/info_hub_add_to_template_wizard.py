# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies (<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions (<https://www.cybrosys.com>)
#
#    This program is free software: you can modify it under the terms of the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful, but
#    WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################

from odoo import fields, models


class InformationAddToTemplateWizard(models.TransientModel):
    _name = 'info.hub.add.to.template.wizard'
    _description = 'Add Article to Template'

    article_id = fields.Many2one(
        comodel_name='info.hub.article',
        string='Article',
        required=True,
        readonly=True,
        help='The article to be converted into a template.',
    )
    template_category_id = fields.Many2one(
        comodel_name='info.hub.template.category',
        string='Category',
        required=True,
        help='The category where the template will be organized.',
    )

    def action_create_template(self):
        self.ensure_one()
        self.env['info.hub.article'].add_article_to_templates(
            self.article_id.id,
            self.template_category_id.id,
        )
        return {'type': 'ir.actions.act_window_close'}
