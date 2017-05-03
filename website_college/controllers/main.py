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
		return request.render("website_college.home_page", {})

	@http.route(['/page/alumni'], type='http', auth="public", website=True)
	def alumni(self, **kwargs):
		"""
		Function render the page alumni
		:param kwargs:
		:return:
		"""
		return request.render("website_college.alumni", {'alumni': True})

	@http.route(['/page/courses'], type='http', auth="public", website=True)
	def courses(self, **kwargs):
		"""
		Function renders the page courses
		:param kwargs:
		:return:
		"""
		return request.render("website_college.course", {'course': True})

	@http.route(['/page/facilities'], type='http', auth="public", website=True)
	def facilities(self, **kwargs):
		"""
		Function renders the facilities page
		:param kwargs:
		:return:
		"""
		return request.render("website_college.facility", {'facilities': True})

	@http.route(['/page/gallery'], type='http', auth="public", website=True)
	def gallery(self, **kwargs):
		"""
		Function loads the gallery page
		:param kwargs:
		:return:
		"""
		return request.render("website_college.gallery", {'gallery': True})

	@http.route('/page/aboutus', type='http', auth="public", website=True)
	def aboutus(self, **kwargs):
		"""
		Function renders the aboutus page
		:param kwargs:
		:return:
		"""
		return request.render("website.aboutus", {'aboutus': True})

	@http.route('/page/contactus', type='http', auth="public", website=True)
	def contactus(self, **opt):
		"""
		Function loads the custom contactus page
		:param opt:
		:return:
		"""
		return request.render("website.contactus", {'contactus': True})
