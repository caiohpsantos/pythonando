from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.contrib import auth
from django.contrib.auth.models import User
from django.contrib.messages import constants
from django.contrib import messages


def cadastro(request):
    if request.method == "GET":
        return render(request, 'cadastro.html')

    elif request.method == "POST":
        usuario = request.POST.get('username')
        user = User.objects.filter(username=usuario)
        if user.exists():
            messages.add_message(request, constants.ERROR,
                                 'Usuário já está cadastrado')
            return redirect('/usuarios/cadastro')
        senha = request.POST.get('senha')
        confirmar_senha = request.POST.get('confirmar_senha')
        if not senha == confirmar_senha:
            messages.add_message(request, constants.ERROR,
                                 'As senhas são diferentes')
            return redirect('/usuarios/cadastro')

        try:
            User.objects.create_user(
                username=usuario,
                password=confirmar_senha

            )
            return redirect('/usuarios/login')
        except:
            messages.add_message(request, constants.ERROR,
                                 'Erro interno do servido. Tente novamente')
            return redirect('/usuarios/cadastro')


def logar(request):
    if request.method == 'GET':
        return render(request, 'logar.html')
    elif request.method == 'POST':
        usuario = request.POST.get('username')
        senha = request.POST.get('senha')
        user = auth.authenticate(request, username=usuario, password=senha)
        if user:
            auth.login(request, user)
            messages.add_message(request, constants.SUCCESS,
                                 'Login efetuado com sucesso')
            return redirect('/flashcard/novo_flashcard/')
        else:
            messages.add_message(request, constants.ERROR,
                                 'Usuário ou senha inválidos')
            return redirect('/usuarios/logar/')


def logout(request):
    auth.logout(request)
    return redirect('/usuarios/logar')
