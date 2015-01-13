# Copyright (c) 2014 Mirantis Inc.
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
# implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from sqlalchemy import distinct

from storyboard.db.api import base as api_base
from storyboard.db import models

SUPPORTED_TYPES = {
    'project': models.Project,
    'project_group': models.ProjectGroup,
    'story': models.Story,
    'task': models.Task
}


def subscription_get(subscription_id):
    return api_base.entity_get(models.Subscription, subscription_id)


def subscription_get_all(**kwargs):
    return api_base.entity_get_all(models.Subscription,
                                   **kwargs)


def subscription_get_all_by_target(target_type, target_id):
    return api_base.entity_get_all(models.Subscription,
                                   target_type=target_type,
                                   target_id=target_id)


def subscription_get_resource(target_type, target_id):
    if target_type not in SUPPORTED_TYPES:
        return None

    return api_base.entity_get(SUPPORTED_TYPES[target_type], target_id)


def subscription_get_count(**kwargs):
    return api_base.entity_get_count(models.Subscription, **kwargs)


def subscription_create(values):
    return api_base.entity_create(models.Subscription, values)


def subscription_delete(subscription_id):
    subscription = subscription_get(subscription_id)

    if subscription:
        api_base.entity_hard_delete(models.Subscription, subscription_id)


def subscription_get_all_subscriber_ids(resource, resource_id):
    '''Test subscription discovery. The tested algorithm is as follows:

    If you're subscribed to a project_group, you will be notified about
    project_group, project, story, and task changes.

    If you are subscribed to a project, you will be notified about project,
    story, and task changes.

    If you are subscribed to a task, you will be notified about changes to
    that task.

    If you are subscribed to a story, you will be notified about changes to
    that story and its tasks.

    :param resource: The name of the resource.
    :param resource_id: The ID of the resource.
    :return: A list of user id's.
    '''
    affected = {
        'project_group': set(),
        'project': set(),
        'story': set(),
        'task': set()
    }

    # Sanity check exit.
    if resource not in affected.keys():
        return set()

    # Make sure the requested resource is going to be handled.
    affected[resource].add(resource_id)

    # Resolve either from story->task or from task->story, so the root
    # resource id remains pristine.
    if resource == 'story':
        # Get this story's tasks
        query = api_base.model_query(models.Task.id) \
            .filter(models.Task.story_id.in_(affected['story']))

        affected['task'] = affected['task'] \
            .union(r for (r, ) in query.all())
    elif resource == 'task':
        # Get this tasks's story
        query = api_base.model_query(models.Task.story_id) \
            .filter(models.Task.id == resource_id)

        affected['story'].add(query.first().story_id)

    # If there are tasks, there will also be projects.
    if affected['task']:
        # Get all the tasks's projects
        query = api_base.model_query(distinct(models.Task.project_id)) \
            .filter(models.Task.id.in_(affected['task']))

        affected['project'] = affected['project'] \
            .union(r for (r, ) in query.all())

    # If there are projects, there will also be project groups.
    if affected['project']:
        # Get all the projects' groups.
        query = api_base.model_query(
            distinct(models.project_group_mapping.c.project_group_id)) \
            .filter(models.project_group_mapping.c.project_id
                    .in_(affected['project']))

        affected['project_group'] = affected['project_group'] \
            .union(r for (r, ) in query.all())

    # Load all subscribers.
    subscribers = set()
    for affected_type in affected:
        query = api_base.model_query(distinct(
            models.Subscription.user_id)) \
            .filter(models.Subscription.target_type == affected_type) \
            .filter(models.Subscription.target_id.in_(affected[affected_type]))

        results = query.all()
        subscribers = subscribers.union(r for (r, ) in results)

    return subscribers
