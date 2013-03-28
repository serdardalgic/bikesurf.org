# -*- coding: utf-8 -*-
# Copyright (c) 2012 Fabian Barkhau <fabian.barkhau@gmail.com>                  
# License: MIT (see LICENSE.TXT file) 


from django.utils.translation import ugettext_lazy as _
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from apps.account.models import Account
from apps.gallery.models import Gallery
from apps.gallery.models import Picture
from apps.team.utils import render_team_response as rtr
from apps.common.shortcuts import render_response
from apps.team.models import Team
from apps.gallery import forms
from apps.gallery import control
from apps.team.utils import assert_member


@login_required
@require_http_methods(["GET", "POST"])
def create(request, **kwargs):
    team_link = kwargs.get("team_link")
    team = team_link and get_object_or_404(Team, link=team_link) or None
    account = get_object_or_404(Account, user=request.user)
    if team:
        assert_member(account, team)
    if request.method == "POST":
        form = forms.Create(request.POST, request.FILES)
        if form.is_valid():
            gallery = control.create(account, form.cleaned_data["image"], team)
            prefix = team and "/%s" % team.link or ""
            url = "%s/gallery/list/%s" % (prefix, gallery.id)
            return HttpResponseRedirect(url)
    else:
        form = forms.Create()
    args = { 
        "form" : form, "form_title" : _("GALLERY_CREATE"), 
        "multipart_form" : True 
    }
    if team:
        return rtr(team, None, request, "common/form.html", args)
    else:
        return render_response(request, "common/form.html", args)


@login_required
@require_http_methods(["GET", "POST"])
def delete(request, **kwargs):
    team_link = kwargs.get("team_link")
    gallery_id = kwargs["gallery_id"]
    pass


@login_required
@require_http_methods(["GET", "POST"])
def primary(request, **kwargs):
    team_link = kwargs.get("team_link")
    gallery_id = kwargs["gallery_id"]
    pass


@login_required
@require_http_methods(["GET", "POST"])
def add(request, **kwargs):
    team_link = kwargs.get("team_link")
    gallery_id = kwargs["gallery_id"]
    pass


@login_required
@require_http_methods(["GET", "POST"])
def remove(request, **kwargs):
    team_link = kwargs.get("team_link")
    picture_id = kwargs["picture_id"]
    pass


@login_required
@require_http_methods(["GET", "POST"])
def update(request, **kwargs):
    team_link = kwargs.get("team_link")
    picture_id = kwargs["picture_id"]
    pass


@require_http_methods(["GET"])
def list(request, **kwargs):
    team_link = kwargs.get("team_link")
    gallery_id = kwargs["gallery_id"]
    team = team_link and get_object_or_404(Team, link=team_link) or None
    gallery = get_object_or_404(Gallery, id=gallery_id)
    pictures = gallery.pictures.all()
    args = { "gallery" : gallery, "pictures" : pictures }
    if team:
        return rtr(team, None, request, "gallery/list.html", args)
    else:
        return render_response(request, "gallery/list.html", args)


@require_http_methods(["GET"])
def view(request, **kwargs):
    team_link = kwargs.get("team_link")
    picture_id = kwargs["picture_id"]
    team = team_link and get_object_or_404(Team, link=team_link) or None
    picture = get_object_or_404(Picture, id=picture_id)
    args = { "picture" : picture }
    if team:
        return rtr(team, None, request, "gallery/view.html", args)
    else:
        return render_response(request, "gallery/view.html", args)


