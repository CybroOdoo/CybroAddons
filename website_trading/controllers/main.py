# -*- coding: utf-8 -*-
from openerp.addons.web.controllers import main
from openerp import http
from openerp.http import request


class Website(main.Home):
	@http.route(['/page/homepage'], type='http', auth="public", website=True)
	def home(self, **kwargs):
		"""
		Overrided function which loads our custom home page templates
		:param kwargs:
		:return:
		"""
		return request.render("website_trading.home", {})
