# -*- coding: utf-8 -*-
# Copyright (c) 2012 Fabian Barkhau <fabian.barkhau@gmail.com>                  
# License: MIT (see LICENSE.TXT file) 


from django.shortcuts import get_object_or_404
from django.utils.translation import ugettext_lazy as _
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.http import HttpResponseRedirect

from apps.common.shortcuts import render_response
from apps.account.models import Account
from apps.team.models import Team
from apps.bike.models import Bike
from apps.team.utils import render_team_response as rtr
from apps.team.utils import assert_member
from apps.borrow.models import Borrow
from apps.borrow import forms
from apps.borrow import control


def _get_team_models(request, team_link, borrow_id):
    team = get_object_or_404(Team, link=team_link)
    account = get_object_or_404(Account, user=request.user)
    assert_member(account, team)
    borrow = get_object_or_404(Borrow, id=borrow_id)
    return team, account, borrow


@login_required
@require_http_methods(["GET"])
def lender_list(request, team_link):
    team = get_object_or_404(Team, link=team_link)
    account = get_object_or_404(Account, user=request.user)
    assert_member(account, team)
    args = { "borrows" : Borrow.objects.filter(team=team) }
    return rtr(team, "borrows", request, "borrow/list.html", args)


@login_required
@require_http_methods(["GET"])
def borrower_list(request):
    account = get_object_or_404(Account, user=request.user)
    args = { "borrows" : Borrow.objects.filter(borrower=account) }
    return render_response(request, "borrow/list.html", args)


@login_required
@require_http_methods(["GET", "POST"])
def create(request, team_link, bike_id):
    team = get_object_or_404(Team, link=team_link)
    account = get_object_or_404(Account, user=request.user)
    bike = get_object_or_404(Bike, id=bike_id)
    if request.method == "POST":
        form = forms.Create(request.POST, bike=bike)
        if form.is_valid():
            borrow = control.create(account, bike,
                                    form.cleaned_data["start"],
                                    form.cleaned_data["finish"],
                                    form.cleaned_data["note"].strip())
            return HttpResponseRedirect("/borrow/view/%s" % borrow.id)
    else:
        form = forms.Create(bike=bike)
    args = { "form" : form, "form_title" : _("BORROW_CREATE") }
    return rtr(team, "borrows", request, "common/form.html", args)


@login_required
@require_http_methods(["GET", "POST"])
def respond(request, team_link, borrow_id):
    team, account, borrow = _get_team_models(request, team_link, borrow_id)
    if request.method == "POST":
        form = forms.Respond(request.POST, borrow=borrow, account=account)
        if form.is_valid():
            control.respond(account, borrow, form.cleaned_data["response"], 
                            form.cleaned_data["note"].strip())
            url = "/%s/borrow/view/%s" % (team.link, borrow.id)
            return HttpResponseRedirect(url)
    else:
        form = forms.Respond(borrow=borrow, account=account)
    args = { "form" : form, "form_title" : _("BORROW_RESPOND") }
    return rtr(team, "borrows", request, "common/form.html", args)


@login_required
@require_http_methods(["GET", "POST"])
def lender_cancel(request, team_link, borrow_id):
    team, account, borrow = _get_team_models(request, team_link, borrow_id)
    if request.method == "POST":
        form = forms.Cancel(request.POST, borrow=borrow, account=account)
        if form.is_valid():
            control.cancel(account, borrow, form.cleaned_data["note"].strip())
            url = "/%s/borrow/view/%s" % (team.link, borrow.id)
            return HttpResponseRedirect(url)
    else:
        form = forms.Cancel(borrow=borrow, account=account)
    args = { "form" : form, "form_title" : _("BORROW_CANCEL") }
    return rtr(team, "borrows", request, "common/form.html", args)


@login_required
@require_http_methods(["GET", "POST"])
def lender_rate(request, team_link, borrow_id):
    team, account, borrow = _get_team_models(request, team_link, borrow_id)
    if request.method == "POST":
        form = forms.Rate(request.POST, borrow=borrow, account=account)
        if form.is_valid():
            rating = form.cleaned_data["rating"]
            note = form.cleaned_data["note"].strip()
            control.lender_rate(account, borrow, rating, note)
            url = "/%s/borrow/view/%s" % (team.link, borrow.id)
            return HttpResponseRedirect(url)
    else:
        form = forms.Rate(borrow=borrow, account=account)
    form_title = u"%s %s" % (_("RATE"), borrow)
    args = { "form" : form, "form_title" : form_title }
    return rtr(team, "borrows", request, "common/form.html", args)


@login_required
@require_http_methods(["GET", "POST"])
def borrower_rate(request, borrow_id):
    account = get_object_or_404(Account, user=request.user)
    borrow = get_object_or_404(Borrow, id=borrow_id)
    if account != borrow.borrower:
        raise PermissionDenied
    if request.method == "POST":
        form = forms.Rate(request.POST, borrow=borrow, account=account)
        if form.is_valid():
            rating = form.cleaned_data["rating"]
            note = form.cleaned_data["note"].strip()
            control.borrower_rate(account, borrow, rating, note)
            return HttpResponseRedirect("/borrow/view/%s" % borrow.id)
    else:
        form = forms.Rate(borrow=borrow, account=account)
    form_title = u"%s %s" % (_("RATE"), borrow)
    args = { "form" : form, "form_title" : form_title }
    return render_response(request, "common/form.html", args)


@login_required
@require_http_methods(["GET"])
def borrower_view(request, borrow_id):
    account = get_object_or_404(Account, user=request.user)
    borrow = get_object_or_404(Borrow, id=borrow_id)
    if account != borrow.borrower:
        raise PermissionDenied
    args = { "borrow" : borrow, "logs" : borrow.logs.all() }
    return render_response(request, "borrow/view.html", args)


@login_required
@require_http_methods(["GET", "POST"])
def borrower_cancel(request, borrow_id):
    account = get_object_or_404(Account, user=request.user)
    borrow = get_object_or_404(Borrow, id=borrow_id)
    if account != borrow.borrower:
        raise PermissionDenied
    if request.method == "POST":
        form = forms.Cancel(request.POST, borrow=borrow, account=account)
        if form.is_valid():
            control.cancel(account, borrow, form.cleaned_data["note"].strip())
            return HttpResponseRedirect("/borrow/view/%s" % borrow.id)
    else:
        form = forms.Cancel(borrow=borrow, account=account)
    args = { "form" : form, "form_title" : _("BORROW_CANCEL") }
    return render_response(request, "common/form.html", args)


@login_required
@require_http_methods(["GET"])
def lender_view(request, team_link, borrow_id):
    team, account, borrow = _get_team_models(request, team_link, borrow_id)
    args = { "borrow" : borrow, "logs" : borrow.logs.all() }
    return rtr(team, "borrows", request, "borrow/view.html", args)


