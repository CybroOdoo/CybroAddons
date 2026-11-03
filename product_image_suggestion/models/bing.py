# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL-3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL-3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL-3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################
import io
import logging
import posixpath
import re
import urllib.parse
import urllib.request
from PIL import Image, UnidentifiedImageError

_logger = logging.getLogger(__name__)


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
        self.headers = {
            'User-Agent': (
                'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.11 '
                '(KHTML, like Gecko) Chrome/23.0.1271.64 Safari/537.11'
            ),
            'Accept': (
                'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
            ),
            'Accept-Charset': 'ISO-8859-1,utf-8;q=0.7,*;q=0.3',
            'Accept-Encoding': 'none',
            'Accept-Language': 'en-US,en;q=0.8',
            'Connection': 'keep-alive',
        }

    def get_filter(self, shorthand):
        """Get the filter from bing"""
        if shorthand in ["line", "linedrawing"]:
            return "+filterui:photo-linedrawing"
        if shorthand == "photo":
            return "+filterui:photo-photo"
        if shorthand == "clipart":
            return "+filterui:photo-clipart"
        if shorthand in ["gif", "animatedgif"]:
            return "+filterui:photo-animatedgif"
        if shorthand == "transparent":
            return "+filterui:photo-transparent"
        return ""

    def save_image(self, link, file_path):
        """Save image safely using Pillow"""
        request = urllib.request.Request(link, None, self.headers)
        data = urllib.request.urlopen(request, timeout=self.timeout).read()
        try:
            img = Image.open(io.BytesIO(data))
            img.verify()
        except UnidentifiedImageError:
            if self.verbose:
                _logger.warning("Skipping invalid image: %s", link)
            return False
        with open(str(file_path), 'wb') as f:
            f.write(data)
        return True

    def download_image(self, link):
        """Download the images using the url obtained"""
        self.download_count += 1
        # Get the image link
        try:
            path = urllib.parse.urlsplit(link).path
            filename = posixpath.basename(path).split('?')[0]
            file_type = filename.split(".")[-1]
            if file_type.lower() not in [
                "jpe", "jpeg", "jfif", "exif", "tiff",
                "gif", "bmp", "png", "webp", "jpg",
            ]:
                file_type = "jpg"

            file_name = f"Image_{self.download_count}.{file_type}"
            self.save_image(link, self.output_dir.joinpath(file_name))
            if self.verbose:
                return link

        except Exception:
            self.download_count -= 1
            self.seen.remove(link)

    def run(self):
        """run the download function"""
        while (self.download_count if self.output_dir else len(self.seen)) < self.limit:
            filter_str = (
                '' if self.filter is None else self.get_filter(self.filter)
            )
            request_url = (
                'https://www.bing.com/images/async?q='
                + urllib.parse.quote_plus(self.query)
                + '&first=' + str(self.page_counter)
                + '&count=' + str(self.limit)
                + '&adlt=' + self.adult
                + '&qft=' + filter_str
            )
            request = urllib.request.Request(
                request_url, None, headers=self.headers
            )
            response = urllib.request.urlopen(request)
            html = response.read().decode('utf8')
            if html == "":
                break
            links = re.findall(r'murl&quot;:&quot;(.*?)&quot;', html)

            for link in links:
                target_count = (
                    self.download_count if self.output_dir else len(self.seen)
                )
                if target_count < self.limit and link not in self.seen:
                    self.seen.add(link)
                    if self.output_dir:
                        self.download_image(link)
            self.page_counter += 1
        return self.seen
