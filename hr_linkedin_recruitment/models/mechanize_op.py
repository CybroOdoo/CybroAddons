# -*- coding: utf-8 -*-
###################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Author: Nilmar Shereef (<shereef@cybrosys.in>)
#    Copyright (C) 2018-TODAY Cybrosys Technologies (<https://www.cybrosys.com>).
#
#    This program is free software: you can modify
#    it under the terms of the GNU Affero General Public License (AGPL) as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
###################################################################################
import logging
import urllib
_logger = logging.getLogger(__name__)
try:
    import mechanize
    from mechanize import _response
    from mechanize import _rfc3986
    import re


    class MechanizeRedirectHandler(mechanize.HTTPRedirectHandler):
        def http_error_302(self, req, fp, code, msg, headers):
            # Code from mechanize._urllib2_fork.HTTPRedirectHandler:
            if 'location' in headers:
                newurl = headers.getheaders('location')[0]
            elif 'uri' in headers:
                newurl = headers.getheaders('uri')[0]
            else:
                return
            newurl = _rfc3986.clean_url(newurl, "latin-1")
            newurl = _rfc3986.urljoin(req.get_full_url(), newurl)

            new = self.redirect_request(req, fp, code, msg, headers, newurl)
            if new is None:
                return

            if hasattr(req, 'redirect_dict'):
                visited = new.redirect_dict = req.redirect_dict
                if (visited.get(newurl, 0) >= self.max_repeats or
                            len(visited) >= self.max_redirections):
                    raise urllib.error.HTTPError(req.get_full_url(), code,
                                    self.inf_msg + msg, headers, fp)
            else:
                visited = new.redirect_dict = req.redirect_dict = {}
            visited[newurl] = visited.get(newurl, 0) + 1

            fp.read()
            fp.close()

            # If the redirected URL doesn't match
            new_url = new.get_full_url()
            if not re.search('^http(?:s)?\:\/\/.*www\.linkedin\.com', new_url):
                return _response.make_response('', headers.items(), new_url, 200, 'OK')
            else:
                return self.parent.open(new)

        http_error_301 = http_error_303 = http_error_307 = http_error_302
        http_error_refresh = http_error_302

except ImportError:
    _logger.warning('Odoo module hr_linkedin_recruitment depends on the several external python package'
                  'Please read the doc/requirement.txt file inside the module.')


