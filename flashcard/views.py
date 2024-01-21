from django.shortcuts import render, redirect, get_object_or_404
from .models import Categoria, Flashcard, Desafio, FlashcardDesafio
from django.http import HttpResponse, Http404
from django.contrib.messages import constants
from django.contrib import messages


def novo_flashcard(request):
    if not request.user.is_authenticated:
        return redirect('/usuarios/logar')
    if request.method == "GET":
        categorias = Categoria.objects.all()
        dificuldades = Flashcard.DIFICULDADE_CHOICES
        flashcards = Flashcard.objects.filter(user=request.user)
        categoria_filtrar = request.GET.get("categoria")
        dificuldade_filtrar = request.GET.get("dificuldade")

        if categoria_filtrar:
            flashcards = flashcards.filter(categoria__id=categoria_filtrar)

        if dificuldade_filtrar:
            flashcards = flashcards.filter(dificuldade=dificuldade_filtrar)

        return render(request, 'novo_flashcard.html', {'categorias': categorias,
                                                       'dificuldades': dificuldades,
                                                       'flashcards': flashcards})

    elif request.method == 'POST':
        pergunta = request.POST.get('pergunta')
        resposta = request.POST.get('resposta')
        categoria = request.POST.get('categoria')
        dificuldade = request.POST.get('dificuldade')

        if len(pergunta.strip()) == 0 or len(resposta.strip()) == 0:
            messages.add_message(
                request,
                constants.ERROR,
                'Preencha os campos de pergunta e resposta',
            )
            return redirect('/flashcard/novo_flashcard')

        flashcard = Flashcard(
            user=request.user,
            pergunta=pergunta,
            resposta=resposta,
            categoria_id=categoria,
            dificuldade=dificuldade,
        )

        flashcard.save()

        messages.add_message(
            request, constants.SUCCESS, 'Flashcard criado com sucesso'
        )
        return redirect('/flashcard/novo_flashcard')


def deletar_flashcard(request, id):
    flashcard = get_object_or_404(Flashcard, id=id)
    # Certifique-se de que o flashcard pertence ao usuário antes de excluí-lo
    if flashcard.user == request.user:
        flashcard.delete()
        messages.add_message(request, constants.SUCCESS,
                             "Flashcard deletado com sucesso!")
        return redirect("/flashcard/novo_flashcard/")

    else:
        messages.add_message(request, constants.ERROR,
                             f"Só é possível deletar flashcards do usuário {request.user}")
        return redirect("/flashcard/novo_flashcard")

    # elif flashcard.DoesNotExist.f:
    #     messages.add_message(request, constants.ERROR,
    #                          "Este card não está cadastrado para seu usuário ou não existe.")
    #     return redirect("/flashcard/novo_flashcard")


def iniciar_desafio(request):
    if request.method == "GET":
        categorias = Categoria.objects.all()
        dificuldades = Flashcard.DIFICULDADE_CHOICES
        return render(request, "iniciar_desafio.html", {'categorias': categorias,
                                                        'dificuldades': dificuldades, })

    elif request.method == "POST":
        titulo = request.POST.get('titulo')
        # ENVIA LISTA DE DADOS, POR ISSO O GET É GETLIST, SE FOR ÚNICO ELEMENTO SÓ O GET
        categorias = request.POST.getlist('categoria')
        dificuldade = request.POST.get('dificuldade')
        qtd_perguntas = request.POST.get('qtd_perguntas')

        desafio = Desafio(
            user=request.user,
            titulo=titulo,
            quantidade_perguntas=qtd_perguntas,
            dificuldade=dificuldade
        )

        desafio.save()

        for categoria in categorias:
            desafio.categoria.add(categoria)

        flashcards = (Flashcard.objects.filter(user=request.user).
                      filter(dificuldade=dificuldade).
                      filter(categoria_id__in=categorias)).order_by('?')

        if flashcards.count() < int(qtd_perguntas):
            messages.add_message(
                request, constants.ERROR, "Há menos flashcards do que solicitado. Cadastre novos ou diminua a quantidade.")
            return redirect('/flashcard/iniciar_desafio')
        else:
            flashcards = flashcards[:int(qtd_perguntas)]

            for f in flashcards:
                flashcard_desafio = FlashcardDesafio(
                    flashcard=f
                )
                flashcard_desafio.save()
                desafio.flashcards.add(flashcard_desafio)
            desafio.save()

            return redirect('/flashcard/listar_desafio')


def listar_desafio(request):
    # Cria os filtros
    todas_categorias = Categoria.objects.all()
    todas_dificuldades = Flashcard.DIFICULDADE_CHOICES

    # filtra os desafios conforme as especificações de categoria e dificuldade
    categoria_filtrar = request.GET.get('categoria')
    dificuldade_filtrar = request.GET.get('dificuldade')
    desafios = Desafio.objects.filter(user=request.user,
                                      categoria=categoria_filtrar,
                                      dificuldade=dificuldade_filtrar)
    # usando cada desafio listado usa o método calcular_status e devolve pro front end
    status = []
    for desafio in desafios:
        situacao_flascards = Desafio.objects.get(id=desafio.id)
        status.append(situacao_flascards.calcular_status())

    desafios_e_status = zip(desafios, status)

    return render(request, 'listar_desafio.html', {"desafios_status": desafios_e_status,
                                                   'categorias': todas_categorias,
                                                   'dificuldades': todas_dificuldades
                                                   })


def desafio(request, id):
    desafio = Desafio.objects.get(id=id)
    if not desafio.user == request.user:
        messages.add_message(
            request, constants.ERROR, "Este desafio não está disponível para seu usuário")
        return redirect('/flashcard/listar_desafio')
    if request.method == "GET":
        acertos = desafio.flashcards.filter(
            respondido=True, acertou=True).count()
        errados = desafio.flashcards.filter(
            respondido=True, acertou=False).count()
        faltantes = desafio.flashcards.filter(respondido=False).count()
        return render(request, 'desafio.html', {"desafio": desafio,
                                                "acertos": acertos,
                                                "errados": errados,
                                                "faltantes": faltantes})


def responder_flashcard(request, id):
    flashcard_desafio = FlashcardDesafio.objects.get(id=id)
    acertou = request.GET.get('acertou')
    desafio_id = request.GET.get('desafio_id')
    if acertou == '1':
        flashcard_desafio.acertou = True
    elif acertou == '0':
        flashcard_desafio.acertou = False
    flashcard_desafio.respondido = True
    flashcard_desafio.save()

    return redirect(f"/flashcard/desafio/{desafio_id}")


def relatorio(request, id):
    desafio = Desafio.objects.get(id=id)
    acertos = desafio.flashcards.filter(
        respondido=True, acertou=True).count()
    errados = desafio.flashcards.filter(
        respondido=True, acertou=False).count()
    dados = [acertos, errados]

    categorias = desafio.categoria.all()
    nome_categorias = [i.nome for i in categorias]

    dados_radar = []
    for categoria in categorias:
        dados_radar.append(desafio.flashcards.filter(
            flashcard__categoria=categoria, acertou=True).count())

    return render(request, 'relatorio.html', {"desafio": desafio,
                                              "dados": dados,
                                              "categoria": nome_categorias,
                                              "dados_radar": dados_radar})
