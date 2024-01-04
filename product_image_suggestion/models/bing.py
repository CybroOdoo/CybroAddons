# -*- coding: utf-8 -*-
##############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<http://www.cybrosys.com>).
#    Author: Vishnu kp(<https://www.cybrosys.com>)
#    you can modify it under the terms of the GNU AFFERO GENERAL
#    PUBLIC LICENSE (AGPL v3), Version 3.

#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC
#    LICENSE (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
import imghdr
import posixpath
import re
import urllib.request
import urllib


class Bing:
    """Download images from bing"""
    def __init__(self, query, limit, output_dir, adult, timeout, filter='',
                 verbose=True):
        self.download_count = 0
        self.query = query
        self.output_dir = output_dir
        self.adult = adult
        self.filter = filter
        self.verbose = verbose
        self.seen = set()
        assert isinstance(limit, int), "limit must be integer"
        self.limit = limit
        assert isinstance(timeout, int), "timeout must be integer"
        self.timeout = timeout

        self.page_counter = 0
        self.headers = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) '
                                      'AppleWebKit/537.11 (KHTML, like Gecko) '
                                      'Chrome/23.0.1271.64 Safari/537.11',
                        'Accept': 'text/html,application/xhtml+xml,'
                                  'application/xml;q=0.9,*/*;q=0.8',
                        'Accept-Charset': 'ISO-8859-1,utf-8;q=0.7,*;q=0.3',
                        'Accept-Encoding': 'none',
                        'Accept-Language': 'en-US,en;q=0.8',
                        'Connection': 'keep-alive'}

    def get_filter(self, shorthand):
        """Get the filter from bing"""
        if shorthand in ["line", "linedrawing"]:
            return "+filterui:photo-linedrawing"
        elif shorthand == "photo":
            return "+filterui:photo-photo"
        elif shorthand == "clipart":
            return "+filterui:photo-clipart"
        elif shorthand in ["gif", "animatedgif"]:
            return "+filterui:photo-animatedgif"
        elif shorthand == "transparent":
            return "+filterui:photo-transparent"
        else:
            return ""

    def save_image(self, link, file_path):
        """Save image to directory"""
        request = urllib.request.Request(link, None, self.headers)
        image = urllib.request.urlopen(request, timeout=self.timeout).read()
        if not imghdr.what(None, image):
            raise ValueError('Invalid image, not saving {}\n'.format(link))
        with open(str(file_path), 'wb') as path_string:
            path_string.write(image)

    def download_image(self, link):
        """Download the images using the url obtained"""
        self.download_count += 1
        # Get the image link
        try:
            path = urllib.parse.urlsplit(link).path
            filename = posixpath.basename(path).split('?')[0]
            file_type = filename.split(".")[-1]
            if file_type.lower() not in ["jpe", "jpeg", "jfif", "exif", "tiff",
                                         "gif", "bmp", "png", "webp", "jpg"]:
                file_type = "jpg"

            self.save_image(link, self.output_dir.joinpath("Image_{}.{}".format(
                str(self.download_count), file_type)))
            if self.verbose:
                return link

        except Exception:
            self.download_count -= 1
            self.seen.remove(link)

    def run(self):
        """run the download function"""
        while self.download_count < self.limit:
            request_url = 'https://www.bing.com/images/async?q=' \
                          + urllib.parse.quote_plus(self.query) \
                          + '&first=' + str(self.page_counter) + '&count=' \
                          + str(self.limit) \
                          + '&adlt=' + self.adult + '&qft=' + (
                              '' if self.filter is None else self.get_filter(
                                  self.filter))
            request = urllib.request.Request(request_url, None,
                                             headers=self.headers)
            response = urllib.request.urlopen(request)
            html = response.read().decode('utf8')
            if html == "":
                break
            links = re.findall('murl&quot;:&quot;(.*?)&quot;', html)

            for link in links:
                if self.download_count < self.limit and link not in self.seen:
                    self.seen.add(link)
                    self.download_image(link)
            self.page_counter += 1
        return self.seen
