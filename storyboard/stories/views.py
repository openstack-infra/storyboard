# Copyright 2013 Thierry Carrez <thierry@openstack.org>
# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.views.decorators.http import require_POST

from storyboard.projects.models import Milestone
from storyboard.projects.models import Project
from storyboard.stories.models import Comment
from storyboard.stories.models import Story
from storyboard.stories.models import StoryTag
from storyboard.stories.models import Task


def dashboard(request):
    recent_bugs = Story.objects.order_by("-id")[:5]
    return render(request, "stories.dashboard.html", {
                  'recent_bugs': recent_bugs,
                  })


def view(request, storyid):
    story = Story.objects.get(id=storyid)
    milestones = Milestone.objects.filter(
        released=False).order_by('branch__release_date')
    return render(request, "stories.view.html", {
                  'story': story,
                  'milestones': milestones,
                  'priorities': Story.STORY_PRIORITIES,
                  'taskstatuses': Task.TASK_STATUSES,
                  })


@login_required
@require_POST
def comment(request, storyid):
    story = Story.objects.get(id=storyid)
    if request.POST.get('comment', False):
        newcomment = Comment(story=story,
                             author=request.user,
                             comment_type="comment",
                             content=request.POST['content'])
        newcomment.save()
    return HttpResponseRedirect('/story/%s' % storyid)


@login_required
@require_POST
def set_priority(request, storyid):
    story = Story.objects.get(id=storyid)
    if 'priority' in request.POST:
        priority = request.POST['priority']
        if int(priority) != story.priority:
            pr = story.get_priority_display()
            story.priority = priority
            story.save()
            # We need to refresh the story to get get_priority_display to work
            story = Story.objects.get(id=storyid)
            msg = "Set priority: %s -> %s" % (pr, story.get_priority_display())
            newcomment = Comment(story=story,
                                 action=msg,
                                 author=request.user,
                                 comment_type="random",
                                 content=request.POST.get('comment', ''))
            newcomment.save()
    return HttpResponseRedirect('/story/%s' % storyid)


@login_required
@require_POST
def add_story(request):
    try:
        newstory = Story(
            title=request.POST['title'],
            description=request.POST['description'],
            creator=request.user,
            priority=0,
        )
        newstory.save()
        proposed_projects = request.POST['projects'].split()
        if proposed_projects:
            master_undefined_milestone = Milestone.objects.get(
                branch__status='M', undefined=True)
            tasks = []
            for project in proposed_projects:
                tasks.append(Task(
                    story=newstory,
                    project=Project.objects.get(name=project),
                    milestone=master_undefined_milestone,
                ))
            Task.objects.bulk_create(tasks)
        proposed_tags = set(request.POST['tags'].split())
        if proposed_tags:
            tags = []
            for tag in proposed_tags:
                tags.append(StoryTag(story=newstory, name=tag))
            StoryTag.objects.bulk_create(tags)
        msg = 'Story created (%s)' % newstory.title
        newcomment = Comment(story=newstory,
                             action=msg,
                             author=request.user,
                             comment_type="star-empty",
                             content='')
        newcomment.save()
    except KeyError:
        pass
    return HttpResponseRedirect('/story/%s' % newstory.id)


@login_required
@require_POST
def add_task(request, storyid):
    story = Story.objects.get(id=storyid)
    try:
        if request.POST['project']:
            if request.POST['milestone']:
                milestone = Milestone.objects.get(id=request.POST['milestone'])
            else:
                milestone = Milestone.objects.get(branch__status='M',
                                                  undefined=True)
            newtask = Task(
                story=story,
                title=request.POST['title'],
                project=Project.objects.get(name=request.POST['project']),
                milestone=milestone,
            )
            newtask.save()
            msg = "Added %s/%s task " % (
                newtask.project.name, newtask.milestone.branch.short_name)
            newcomment = Comment(story=story,
                                 action=msg,
                                 author=request.user,
                                 comment_type="plus-sign",
                                 content=request.POST.get('comment', ''))
            newcomment.save()
    except KeyError:
        pass
    return HttpResponseRedirect('/story/%s' % story.id)


@login_required
@require_POST
def edit_task(request, taskid):
    task = Task.objects.get(id=taskid)
    try:
        actions = []
        if (task.title != request.POST['title']):
            actions.append("title")
            task.title = request.POST['title']
        milestone = Milestone.objects.get(id=int(request.POST['milestone']))
        milestonename = milestone.name
        if (milestone != task.milestone):
            actions.append("milestone -> %s" % milestonename)
            task.milestone = milestone
        status = request.POST['status']
        if (task.status != status):
            task.status = status
            actions.append("status -> %s" % task.get_status_display())
        if not request.POST['assignee']:
            assignee = None
            assigneename = "None"
        else:
            assignee = User.objects.get(username=request.POST['assignee'])
            assigneename = assignee.username
        if (assignee != task.assignee):
            actions.append("assignee -> %s" % assigneename)
            task.assignee = assignee
        if actions:
            msg = "Updated %s/%s task " % (task.project.name,
                                           task.milestone.branch.short_name)
            msg += ", ".join(actions)
            task.save()
            newcomment = Comment(story=task.story,
                                 action=msg,
                                 author=request.user,
                                 comment_type="tasks",
                                 content=request.POST.get('comment', ''))
            newcomment.save()
    except KeyError:
        pass
    return HttpResponseRedirect('/story/%s' % task.story.id)


@login_required
@require_POST
def delete_task(request, taskid):
    task = Task.objects.get(id=taskid)
    task.delete()
    msg = "Deleted %s/%s task" % (task.project.name,
                                  task.milestone.branch.short_name)
    newcomment = Comment(story=task.story,
                         action=msg,
                         author=request.user,
                         comment_type="remove-sign",
                         content=request.POST.get('comment', ''))
    newcomment.save()
    return HttpResponseRedirect('/story/%s' % task.story.id)


@login_required
@require_POST
def edit_story(request, storyid):
    story = Story.objects.get(id=storyid)
    storytags = set(x.name for x in StoryTag.objects.filter(story=story))
    onlytags = True
    try:
        actions = []
        if (story.title != request.POST['title']):
            onlytags = False
            actions.append("title")
            story.title = request.POST['title']
        if (story.description != request.POST['description']):
            onlytags = False
            actions.append("description")
            story.description = request.POST['description']
        proposed_tags = set(request.POST['tags'].split())
        if proposed_tags != storytags:
            actions.append("tags")
            StoryTag.objects.filter(story=story).delete()
            tags = []
            for tag in proposed_tags:
                tags.append(StoryTag(story=story, name=tag))
            StoryTag.objects.bulk_create(tags)
        if actions:
            msg = "Updated story " + ", ".join(actions)
            story.save()
            if onlytags:
                comment_type = "tags"
            else:
                comment_type = "align-left"
            newcomment = Comment(story=story,
                                 action=msg,
                                 author=request.user,
                                 comment_type=comment_type)
            newcomment.save()
    except KeyError as e:
        print(e)
    return HttpResponseRedirect('/story/%s' % story.id)
