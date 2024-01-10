# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Bhagyadev K P (odoo@cybrosys.com)
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
################################################################################
from odoo import fields, models


class ResConfigSettings(models.TransientModel):
	"""Inheriting res_config_settings to add generate_token, pos_token and
	takeaway fields"""
	_inherit = 'res.config.settings'

	generate_token = fields.Boolean(string="Generate Token",
	                                help="This will generate separate token "
	                                     "for all Take Away orders.")
	pos_token = fields.Integer(string="Token",
	                           help='The token will be start from 1.')
	takeaway = fields.Boolean(string="POS Takeaways",
	                          help="This will enable the Take Away feature on"
	                               " POS.",
	                          config_parameter='pos_takeaway.takeaway')

	def get_values(self):
		"""Getting the values"""
		res = super(ResConfigSettings, self).get_values()
		res.update(
			generate_token = self.env['ir.config_parameter'].sudo().get_param(
				'pos_takeaway.generate_token'),
			pos_token=self.env['ir.config_parameter'].sudo().get_param(
				'pos_takeaway.pos_token'),
		)
		return res

	def set_values(self):
		"""Set the values"""
		res = super(ResConfigSettings, self).set_values()
		self.env['ir.config_parameter'].sudo().set_param(
			'pos_takeaway.generate_token', self.generate_token)
		self.env['ir.config_parameter'].sudo().set_param(
			'pos_takeaway.pos_token', self.pos_token or 0)
		return res
