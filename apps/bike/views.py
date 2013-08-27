# -*- coding: utf-8 -*-
# Copyright (c) 2012 Fabian Barkhau <fabian.barkhau@gmail.com>                  
# License: MIT (see LICENSE.TXT file) 


import datetime

from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.utils.translation import ugettext as _
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied

from apps.borrow import control as borrow_control
from apps.team import control as team_control
from apps.common.shortcuts import render_response
from apps.common.shortcuts import chunks
from apps.account.models import Account
from apps.team.models import Team
from apps.bike.models import Bike
from apps.bike import control
from apps.team.utils import render_team_response as rtr
from apps.team.utils import assert_member
from apps.bike import forms


_VIEW = {
    "OVERVIEW" : {
        "template" : "bike/view.html",
        "page_title" : "",
    },
    "BORROWS" :    {
        "template" : "common/list.html",
        "page_title" : _("BIKE_BORROWS"),
    },
}


def _tabs(bike, team, selected, authorized):
    base_link = "/%s/bike/view/%d" % (team.link, bike.id)
    overview = (base_link,              _("OVERVIEW"), selected == "OVERVIEW")
    borrows =  (base_link + "/borrows", _("BORROWS"),  selected == "BORROWS")
    if authorized:
        return [overview, borrows]
    return [overview]


def _get_listing_bikes(request, team, form):
    qs = team.bikes.all()

    # hide reserve and inactive for non team members and non logged in users
    logged_in = request.user.is_authenticated()
    account = logged_in and get_object_or_404(Account, user=request.user) or 0
    if not logged_in or not team_control.is_member(account, team):
        qs = qs.filter(reserve=False, active=True)

    if not form:
        return list(qs)

    # lights 
    lights = form.cleaned_data["lights"]
    if lights:
        qs = qs.filter(lights=True)

    # size
    size = form.cleaned_data["size"]
    if size:
        qs = qs.filter(size=size)

    # filter timeframe
    start = form.cleaned_data["start"]
    finish = form.cleaned_data["finish"]
    if finish and not start:
        today = datetime.datetime.now().date()
        start = today + datetime.timedelta(days=1)
    if start and not finish:
        finish = start + datetime.timedelta(days=7)
    if start and finish:
        qs = qs.exclude(borrows__active=True, borrows__start__range=(start, finish))
        qs = qs.exclude(borrows__active=True, borrows__finish__range=(start, finish))

    return list(qs)


@require_http_methods(["GET"])
def view(request, team_link, bike_id, tab):
    team = team_control.get_or_404(team_link)

    # check user permissions
    requires_login = tab != "OVERVIEW"
    requires_membership = tab != "OVERVIEW"
    logged_in = request.user.is_authenticated()
    if not logged_in and requires_login:
        return HttpResponseRedirect("/accounts/login/?next=%s" % request.path)
    account = logged_in and get_object_or_404(Account, user=request.user)
    if requires_membership and not team_control.is_member(account, team):
        raise PermissionDenied

    # get data
    bike = get_object_or_404(Bike, id=bike_id, team=team)
    authorized = (account and team_control.is_member(account, team))
    template = _VIEW[tab]["template"]
    list_data = None
    if tab == "BORROWS":
        list_data = borrow_control.to_list_data(bike.borrows.all(), team=team)

    args = { 
        "bike" : bike, "list_data" : list_data,
        "page_title" : _VIEW[tab]["page_title"],
        "tabs" : _tabs(bike, team, tab, authorized), 
    }
    return rtr(team, "bikes", request, template, args)


@require_http_methods(["GET", "POST"])
def listing(request, team_link):
    team = team_control.get_or_404(team_link)

    if request.method == "POST":
        form = forms.FilterListing(request.POST)
        if form.is_valid():
            bikes = _get_listing_bikes(request, team, form)
        else:
            bikes = _get_listing_bikes(request, team, None)
    else:
        form = forms.FilterListing()
        bikes = _get_listing_bikes(request, team, None)

    args = { 
        "page_title" : _("BIKES"), "filters" : form,
        "bike_pairs" : list(chunks(bikes, 2))
    }
    return rtr(team, "bikes", request, "bike/list.html", args)


@login_required
@require_http_methods(["GET", "POST"])
def create(request, team_link):
    team = team_control.get_or_404(team_link)
    account = get_object_or_404(Account, user=request.user)
    assert_member(account, team)
    if request.method == "POST":
        form = forms.Create(request.POST, request.FILES, 
                            team=team, account=account)
        if form.is_valid():
            bike = control.create(
                account, team, form.cleaned_data["name"].strip(),
                form.cleaned_data["image"],
                form.cleaned_data["description"].strip(),
                form.cleaned_data["active"], form.cleaned_data["reserve"],
                form.cleaned_data["station"], form.cleaned_data["lockcode"],
                form.cleaned_data["size"], form.cleaned_data["lights"], 
            )
            url = "/%s/bike/view/%s" % (team.link, bike.id)
            return HttpResponseRedirect(url)
    else:
        form = forms.Create(team=team, account=account)
    args = { 
        "form" : form, "form_title" : _("BIKE_CREATE"), "multipart_form" : True, 
        "cancel_url" : "/%s/bikes" % team.link
    }
    return rtr(team, "bikes", request, "common/form.html", args)


@login_required
@require_http_methods(["GET", "POST"])
def edit(request, team_link, bike_id):
    team = team_control.get_or_404(team_link)
    account = get_object_or_404(Account, user=request.user)
    assert_member(account, team)
    bike = get_object_or_404(Bike, id=bike_id, team=team)
    if request.method == "POST":
        form = forms.Edit(request.POST, bike=bike, account=account)
        if form.is_valid():
            control.edit(
                account, bike,
                form.cleaned_data["name"].strip(),
                form.cleaned_data["description"].strip(),
                form.cleaned_data["active"], form.cleaned_data["reserve"],
                form.cleaned_data["station"], form.cleaned_data["lockcode"],
                form.cleaned_data["size"], form.cleaned_data["lights"],
            )
            url = "/%s/bike/view/%s" % (team.link, bike.id)
            return HttpResponseRedirect(url)
    else:
        form = forms.Edit(bike=bike, account=account)
    args = { 
        "form" : form, "form_title" : _("BIKE_EDIT"),
        "cancel_url" : "/%s/bike/view/%s" % (team.link, bike.id)
    }
    return rtr(team, "bikes", request, "common/form.html", args)


@login_required
@require_http_methods(["GET", "POST"])
def delete(request, team_link, bike_id):
    team = team_control.get_or_404(team_link)
    account = get_object_or_404(Account, user=request.user)
    bike = get_object_or_404(Bike, id=bike_id, team=team)

    if request.method == "POST":
        form = forms.Delete(request.POST, bike=bike, account=account)
        if form.is_valid():
            control.delete(account, bike)
            return HttpResponseRedirect("/%s/bikes" % team.link)
    else:
        form = forms.Delete(bike=bike, account=account)
    args = { 
        "form" : form, "form_title" : _("BIKE_DELETE?"), 
        "form_subtitle" : bike.name, 
        "cancel_url" : "/%s/bike/view/%s" % (team.link, bike.id)
    }
    return rtr(team, "bikes", request, "common/form.html", args)



