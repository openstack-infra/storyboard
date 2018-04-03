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


import abc
import copy
import json
import os
import six
import smtplib

from email.utils import make_msgid
from jinja2.exceptions import TemplateNotFound
from oslo_config import cfg
from oslo_log import log
from socket import getfqdn

import storyboard.db.api.base as db_base
from storyboard.db.api.subscriptions import subscription_get_all_subscriber_ids
from storyboard.db.api import timeline_events as events_api
import storyboard.db.models as models
from storyboard.plugin.email.base import EmailPluginBase
from storyboard.plugin.email.factory import EmailFactory
from storyboard.plugin.email import smtp_client as smtp
from storyboard.plugin.event_worker import WorkerTaskBase


LOG = log.getLogger(__name__)

CONF = cfg.CONF


@six.add_metaclass(abc.ABCMeta)
class EmailWorkerBase(EmailPluginBase, WorkerTaskBase):
    """An abstract email construction worker.

    Abstract class that encapsulates common functionality needed in
    building emails off of our event queue.
    """

    def handle(self, session, author, method, url, path, query_string, status,
               resource, resource_id, sub_resource=None, sub_resource_id=None,
               resource_before=None, resource_after=None):
        """Handle an event.

        :param session: An event-specific SQLAlchemy session.
        :param author: The author's user record.
        :param method: The HTTP Method.
        :param url: The Referer header from the request.
        :param path: The full HTTP Path requested.
        :param query_string: The HTTP query string from the request.
        :param status: The returned HTTP Status of the response.
        :param resource: The resource type.
        :param resource_id: The ID of the resource.
        :param sub_resource: The subresource type.
        :param sub_resource_id: The ID of the subresource.
        :param resource_before: The resource state before this event occurred.
        :param resource_after: The resource state after this event occurred.
        """

        # We only care about a subset of resource types.
        if resource not in ['task', 'project_group', 'project', 'story',
                            'branch', 'milestone', 'tag', 'timeline_event']:
            return

        if resource == 'timeline_event':
            if resource_after['worklist_id'] is None:
                return
            resource = 'worklist'
            resource_id = resource_after['worklist_id']
            resource_after['event_info'] = json.loads(
                resource_after['event_info'])

            if 'created' not in resource_after['event_type']:
                method = 'PUT'

            if 'contents' in resource_after['event_type']:
                sub_resource = 'item'

            if 'filters' in resource_after['event_type']:
                sub_resource = 'filter'

            if 'permission' in resource_after['event_type']:
                sub_resource = 'permission'

        # We only care about PUT, POST, and DELETE requests that do not
        # result in errors or redirects.
        if method == 'GET' or status >= 300:
            return

        # We only care if the current resource has subscribers.
        if resource == 'task' and method == 'DELETE':
            # FIXME(SotK): Workaround the fact that the task won't be in the
            # database anymore if it has been deleted.
            # We should archive instead of delete to solve this.
            # NOTE: People who are only subscribed to the task (not the story)
            # won't get an email.
            subscribers = self.get_subscribers(session, 'story',
                                               resource_before['story_id'])
        else:
            subscribers = self.get_subscribers(session, resource, resource_id)
        if not subscribers:
            return

        # Pass our values on to the handler.
        self.handle_email(session=session,
                          author=author,
                          subscribers=subscribers,
                          method=method,
                          url=url,
                          status=status,
                          path=path,
                          query_string=query_string,
                          resource=resource,
                          resource_id=resource_id,
                          sub_resource=sub_resource,
                          sub_resource_id=sub_resource_id,
                          resource_before=resource_before,
                          resource_after=resource_after)

    @abc.abstractmethod
    def handle_email(self, session, author, subscribers, method, url, path,
                     query_string, status, resource, resource_id,
                     sub_resource=None, sub_resource_id=None,
                     resource_before=None, resource_after=None):
        """Handle an email notification for the given subscribers.

        :param session: An event-specific SQLAlchemy session.
        :param author: The author's user record.
        :param subscribers: A list of subscribers that should receive an email.
        :param method: The HTTP Method.
        :param url: The Referer header from the request.
        :param path: The full HTTP Path requested.
        :param query_string: The query string from the request.
        :param status: The returned HTTP Status of the response.
        :param resource: The resource type.
        :param resource_id: The ID of the resource.
        :param sub_resource: The subresource type.
        :param sub_resource_id: The ID of the subresource.
        :param resource_before: The resource state before this event occurred.
        :param resource_after: The resource state after this event occurred.
        """

    def get_subscribers(self, session, resource, resource_id):
        """Get a list of users who are subscribed to the resource,
        whose email address is valid, and whose email preferences indicate
        that they'd like to receive non-digest email.
        """
        subscribers = []

        # Resolve all the subscriber ID's.
        subscriber_ids = subscription_get_all_subscriber_ids(resource,
                                                             resource_id,
                                                             session=session)
        users = db_base.model_query(models.User, session) \
            .filter(models.User.id.in_(subscriber_ids)).all()

        for user in users:
            if not self.get_preference('plugin_email_enable', user) == 'true':
                continue
            subscribers.append(user)

        return subscribers

    def get_preference(self, name, user):
        if name not in user.preferences:
            return None
        return user.preferences[name].cast_value

    def get_changed_properties(self, original, new):
        """Shallow comparison diff.

        This method creates a shallow comparison between two dicts,
        and returns two dicts containing only the changed properties from
        before and after. It intentionally excludes created_at and updated_at,
        as those aren't true 'values' so to say.
        """

        # Clone our value arrays, since we might return them.
        before = copy.copy(original) or None
        after = copy.copy(new) or None

        # Strip out protected parameters
        for protected in ['created_at', 'updated_at']:
            if before and protected in before:
                del before[protected]
            if after and protected in after:
                del after[protected]

        # Sanity check, null values.
        if not before or not after:
            return before, after

        # Collect all the keys
        before_keys = set(before.keys())
        after_keys = set(after.keys())
        keys = before_keys | after_keys

        # Run the comparison.
        for key in keys:
            if key not in before:
                before[key] = None
            if key not in after:
                after[key] = None

            if after[key] == before[key]:
                del after[key]
                del before[key]

        return before, after


class SubscriptionEmailWorker(EmailWorkerBase):
    """This worker plugin generates individual event emails for users who
    have indicated that they wish to receive emails, but don't want digests.
    """

    def handle_email(self, session, author, subscribers, method, url, path,
                     query_string, status, resource, resource_id,
                     sub_resource=None, sub_resource_id=None,
                     resource_before=None, resource_after=None):
        """Send an email for a specific event.

        We assume that filtering logic has already occurred when this method
        is invoked.

        :param session: An event-specific SQLAlchemy session.
        :param author: The author's user record.
        :param subscribers: A list of subscribers that should receive an email.
        :param method: The HTTP Method.
        :param url: The Referer header from the request.
        :param path: The full HTTP Path requested.
        :param query_string: The query string from the request.
        :param status: The returned HTTP Status of the response.
        :param resource: The resource type.
        :param resource_id: The ID of the resource.
        :param sub_resource: The subresource type.
        :param sub_resource_id: The ID of the subresource.
        :param resource_before: The resource state before this event occurred.
        :param resource_after: The resource state after this event occurred.
        """

        email_config = CONF.plugin_email

        # Retrieve the template names.
        (subject_template, text_template, html_template) = \
            self.get_templates(method=method,
                               resource_name=resource,
                               sub_resource_name=sub_resource)

        # Build our factory. If an HTML template exists, add it. If it can't
        # find the template, skip.
        try:
            factory = EmailFactory(sender=email_config.sender,
                                   subject=subject_template,
                                   text_template=text_template)
        except TemplateNotFound:
            LOG.error("Templates not found [%s, %s]" % (subject_template,
                                                        text_template))
            return

        # Try to add an HTML template
        try:
            factory.add_text_template(html_template, 'html')
        except TemplateNotFound:
            LOG.debug('Template %s not found' % (html_template,))

        # If there's a reply-to in our config, add that.
        if email_config.reply_to:
            factory.add_header('Reply-To', email_config.reply_to)

        # If there is a fallback URL configured, use it if needed
        if email_config.default_url and url is None:
            url = email_config.default_url

        # Resolve the resource instance
        resource_instance = self.resolve_resource_by_name(session, resource,
                                                          resource_id)
        sub_resource_instance = self.resolve_resource_by_name(session,
                                                              sub_resource,
                                                              sub_resource_id)

        # Set In-Reply-To message id for 'task', 'story', and
        # 'worklist' resources
        story_id = None
        worklist_id = None
        if resource == 'task' and method == 'DELETE':
            # FIXME(pedroalvarez): Workaround the fact that the task won't be
            # in the database anymore if it has been deleted.
            # We should archive instead of delete to solve this.
            story_id = resource_before['story_id']
            created_at = self.resolve_resource_by_name(session, 'story',
                story_id).created_at
        elif resource == 'task':
            story_id = resource_instance.story.id
            created_at = resource_instance.story.created_at
        elif resource == 'story':
            story_id = resource_instance.id
            created_at = resource_instance.created_at
        elif resource == 'worklist':
            worklist_id = resource_instance.id
            created_at = resource_instance.created_at

        if story_id and created_at:
            thread_id = "<storyboard.story.%s.%s@%s>" % (
                created_at.strftime("%Y%m%d%H%M"),
                story_id,
                getfqdn()
            )
        elif worklist_id and created_at:
            thread_id = "<storyboard.worklist.%s.%s@%s>" % (
                created_at.strftime("%Y%m%d%H%M"),
                story_id,
                getfqdn()
            )
        else:
            thread_id = make_msgid()

        factory.add_header("In-Reply-To", thread_id)
        factory.add_header("X-StoryBoard-Subscription-Type", resource)

        # Figure out the diff between old and new.
        before, after = self.get_changed_properties(resource_before,
                                                    resource_after)

        # For each subscriber, create the email and send it.
        with smtp.get_smtp_client() as smtp_client:
            for subscriber in subscribers:

                # Make sure this subscriber's preferences indicate they want
                # email and they're not receiving digests.
                if not self.get_preference('plugin_email_enable', subscriber) \
                        or self.get_preference('plugin_email_digest',
                                               subscriber):
                    continue

                send_notification = self.get_preference(
                    'receive_notifications_worklists', subscriber)
                if send_notification != 'true' and story_id is None:
                    continue

                # Don't send a notification if the user isn't allowed to see
                # the thing this event is about.
                if 'event_type' in resource:
                    event = events_api.event_get(
                        resource['id'],
                        current_user=subscriber.id,
                        session=session)
                    if not events_api.is_visible(
                            event, subscriber.id, session=session):
                        continue

                try:
                    # Build an email.
                    message = factory.build(recipient=subscriber.email,
                                            author=author,
                                            resource=resource_instance,
                                            sub_resource=sub_resource_instance,
                                            url=url,
                                            query_string=query_string,
                                            before=before,
                                            after=after)
                    # Send the email.
                    from_addr = message.get('From')
                    to_addrs = message.get('To')

                    try:
                        smtp_client.sendmail(from_addr=from_addr,
                                             to_addrs=to_addrs,
                                             msg=message.as_string())
                    except smtplib.SMTPException as e:
                        LOG.error('Cannot send email, discarding: %s' % (e,))
                except Exception as e:
                    # Skip, keep going.
                    LOG.error("Cannot schedule email: %s" % (e.message,))

    def get_templates(self, method, resource_name, sub_resource_name=None):
        """Return the email templates for the given resource.

        This method builds the names of templates for a provided resource
        action. The template folder structure is as follows:

        /{{resource_name}}/{{method}}_subject.txt
        /{{resource_name}}/{{method}}.txt
        /{{resource_name}}/{{method}}.html (optional)

        For subresources, it is as follows:
        /{{resource_name}}/{{subresource_name}}/{{method}}_subject.txt
        /{{resource_name}}/{{subresource_name}}/{{method}}.txt
        /{{resource_name}}/{{subresource_name}}/{{method}}.html (optional)
        """
        ## TODO(krotscheck): Templates can also resolve by user language.

        if sub_resource_name:
            base_template = os.path.join(resource_name, sub_resource_name)
        else:
            base_template = resource_name

        base_file = '%s' % (method,)

        subject_template = os.path.join(base_template,
                                        '%s_subject.txt' % (base_file,))
        text_template = os.path.join(base_template,
                                     '%s.txt' % (base_file,))
        html_template = os.path.join(base_template,
                                     '%s.html' % (base_file,))

        return subject_template, text_template, html_template
