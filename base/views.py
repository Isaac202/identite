from django.shortcuts import render

# Create your views here.


from django.shortcuts import render

# Create your views here.

def cadastrar_venda(request):
    if request.method == 'POST':
        # Aqui você pode tratar os dados do formulário
        # Você pode acessar os dados do formulário com request.POST
        pass

    return render(request, 'cadastrar_venda.html')