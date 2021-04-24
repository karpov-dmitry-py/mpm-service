from django.shortcuts import render
from django.contrib.auth.decorators import login_required


def home(request):
    context = {'title': 'Main page'}
    return render(request, 'users/home.html', context)


@login_required
def view_account(request):
    context = {'title': 'Профиль'}
    return render(request, 'users/account.html', context)
