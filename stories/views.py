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
from django.views.decorators.http import require_POST
from django.http import HttpResponseRedirect, HttpResponseForbidden
from django.shortcuts import render
from django.contrib.auth.models import User
from projects.models import Milestone
from stories.models import Story, Task, Comment

def dashboard(request):
    return render(request, "stories.dashboard.html")


def view(request, storyid):
    story = Story.objects.get(id=storyid)
    milestones = Milestone.objects.all()
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
    if 'content' in request.POST:
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
        story.priority = request.POST['priority']
        story.save()
    return HttpResponseRedirect('/story/%s' % storyid)

@login_required
@require_POST
def edit_task(request, taskid):
    task = Task.objects.get(id=taskid)
    try:
        actions = []
        if (task.title != request.POST['title']):
            actions.append("task title")
            task.title = request.POST['title']
        milestone = Milestone.objects.get(id=request.POST['milestone'])
        if (milestone != task.milestone):
            actions.append("milestone -> %s" % milestone.name)
            task.milestone = milestone
        status = request.POST['status']
        if (task.status != status):
            task.status = status
            actions.append("status -> %s" % task.get_status_display())
        assignee = User.objects.get(username=request.POST['assignee'])
        if (assignee != task.assignee):
            actions.append("assignee -> %s" % assignee.username)
            task.assignee = assignee
        if actions:
            msg = "Updated " + ", ".join(actions)
            task.save()
            newcomment = Comment(story=task.story,
                                 action=msg,
                                 author=request.user,
                                 comment_type="tasks",
                                 content=request.POST.get('comment', ''))
            newcomment.save()
    except KeyError as e:
        print e
    return HttpResponseRedirect('/story/%s' % task.story.id)
