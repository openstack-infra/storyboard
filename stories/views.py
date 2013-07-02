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

from stories.models import Story, Comment

def dashboard(request):
    return render(request, "stories.dashboard.html")


def view(request, storyid):
    story = Story.objects.get(id=storyid)
    return render(request, "stories.view.html", {
                  'story': story,
                  'priorities': Story.STORY_PRIORITIES,
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
