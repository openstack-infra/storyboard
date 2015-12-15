# Copyright (c) 2015 Hewlett-Packard Development Company, L.P.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied. See the License for the specific language governing permissions and
# limitations under the License.


import collections
import re
import six

from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formatdate

from jinja2 import Environment
from jinja2 import PackageLoader


class EmailFactory(object):
    """An email rendering utility, which takes a default Jinja2 templates,
    a data dict, and builds an RFC 2046 compliant email. We enforce several
    constant headers here, in order to reduce the amount of replicated code.
    """

    def __init__(self, sender, subject, text_template,
                 template_package='storyboard.plugin.email'):
        """Create a new instance of the email renderer.

        :param sender: The sender of this email.
        :param subject: The subject of this email, which may be templated.
        :param text_template: A Jinja2 template for the raw text content.
        :return:
        """
        super(EmailFactory, self).__init__()

        # Build our template classpath loader and template cache. Default
        # text encoding is UTF-8. The use of OrderedDict is important,
        # as the Email RFC specifies rendering priority based on order.
        self.template_cache = collections.OrderedDict()
        self.env = Environment(loader=PackageLoader(template_package,
                                                    'templates'))

        # Store internal values.
        self.sender = sender
        self.subject = self.env.get_template(subject)
        self.headers = dict()

        # Add the default text template.
        self.add_text_template(text_template, mime_subtype='plain')

        # Declare default headers.
        self.headers['Auto-Submitted'] = 'auto-generated'

    def add_text_template(self, template, mime_subtype='plain'):
        """Add a text/* template type to this email engine.

        :param template: The name of the template.
        :param mime_subtype: The mime subtype. ex: text/html -> html
        """
        self.template_cache[mime_subtype] = self.env.get_template(template)

    def add_header(self, name, value):
        """Add a custom header to the factory.

        :param name: The name of the header.
        :param value: The value of the header.
        """
        self.headers[name] = value

    def build(self, recipient, **kwargs):
        """Build this email and return the Email Instance.

        :param recipient: The recipient of the email.
        :param kwargs: Additional key/value arguments to be rendered.
        :return: The email instance.
        """

        # Create message container as multipart/alternative.
        msg = MIMEMultipart('alternative')
        msg['From'] = self.sender
        msg['To'] = recipient
        msg['Date'] = formatdate(localtime=True)

        # Render the subject template. Add length and \r\n sanity check
        # replacements. While we could fold the subject line, if our subject
        # lines are longer than 78 characters nobody's going to read them all.
        subject = self.subject.render(**kwargs)
        subject = re.sub(r'\r?\n', ' ', subject)

        if len(subject) > 78:
            subject = subject[0:75] + '...'
        msg['Subject'] = subject

        # Iterate and render over all additional headers.
        for key, value in six.iteritems(self.headers):
            try:
                msg.replace_header(key, value)
            except KeyError:
                msg.add_header(key, value)

        # Render and attach our templates.
        for type, template in six.iteritems(self.template_cache):
            body_part = template.render(**kwargs)
            msg.attach(MIMEText(body_part, type, "utf-8"))

        return msg
