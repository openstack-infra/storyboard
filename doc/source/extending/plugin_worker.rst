==========================================
Extending StoryBoard: Event Worker Plugins
==========================================

Overview
--------

It is sometimes useful to have a method to react to StoryBoard's API events.
This can be done using Event Worker plugins, which recieve a notification
whenever a POST, PUT, or DELETE action occurs on the API. The plugin can then
decide how to process each event asynchronously so as not to impact the
stability of the API.

Your workers will be detected by `storyboard-worker-daemon` when it starts,
and a number of worker processes will be created. When a daemon finds a
message in the Rabbit queue, it passes the message to the handle() function
of each worker plugin it has found.

Note: In order for event worker plugins to work, your StoryBoard config file
will need to contain `enable_notifications = True`.

Event Worker Plugin Quickstart
------------------------------

Step 1: Create a new python project using setuptools
####################################################

This is left as an exercise to the reader. Don't forget to include storyboard
as a requirement.

Step 2: Implement your plugin
#############################

Add a registered entry point in your plugin's `setup.cfg`. The name should be
reasonably unique::

    [entry_points]
    storyboard.plugin.worker =
         my-worker-plugin = my.namespace.plugin:MyEventWorker

Then, implement your plugin by extending `WorkerTaskBase`. You may register
your own configuration groups, please see
`oslo.config <http://docs.openstack.org/developer/oslo.config/api/oslo.config.cfg.html>`_
for more details.::

    from storyboard.plugin.event_worker import WorkerTaskBase

    class MyEventWorker(WorkerTaskBase):

        def enabled(self):
            '''This method should return whether the plugin is enabled and
            configured. It has access to self.config, which is a reference to
            storyboard's global configuration object.
            '''
            return True


        def handle(self, session, author, method, path, status, resource,
                   resource_id, sub_resource=None, sub_resource_id=None,
                   resource_before=None, resource_after=None):
            """This method takes information about an API event and does
            something with it, for example creating a SubscriptionEvent
            in the database for everyone subscribed to the affected resource.

            :param session: An event-specific SQLAlchemy session.
            :param author: The author's user record.
            :param method: The HTTP Method.
            :param path: The full HTTP Path requested.
            :param status: The returned HTTP Status of the response.
            :param resource: The resource type.
            :param resource_id: The ID of the resource.
            :param sub_resource: The subresource type.
            :param sub_resource_id: The ID of the subresource.
            :param resource_before: The resource state before this event occurred.
            :param resource_after: The resource state after this event occurred.
            """
            if resource == 'timeline_event':
                event = db_api.entity_get(models.TimeLineEvent, resource_id,
                                          session=session)
                subscribers = sub_api.subscription_get_all_subscriber_ids(
                    'story', event.story_id, session=session)

                for user_id in subscribers:
                    event_info = event.event_info
                    db_api.entity_create(models.SubscriptionEvents, {
                        "author_id": author.id,
                        "subscriber_id": user_id,
                        "event_type": event.event_type,
                        "event_info": event_info
                    }, session=session)


Step 3: Install your plugin
###########################

Finally, install your plugin, which may require you switch into storyboard's
virtual environment. Pip should automatically register your plugin::

    pip install my-storyboard-plugin
