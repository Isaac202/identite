$(document).ready(function() {
    console.log('panel_client_form.js loaded');
    initializeForm();
});

function initializeForm() {
    setupMasks();
    setupFormSubmission();
    setupCepLookup();
    setupCnpjLookup();
}

function setupMasks() {
    $('#telefone').mask('(00) 0 0000-0000');
    $('#cpf').mask('000.000.000-00', {reverse: true});
    $('#cnpj').mask('00.000.000/0000-00', {reverse: true});
    $('#data_nascimento').mask('00/00/0000');
    $('#cep').mask('00000-000');
}

function setupFormSubmission() {
    $('#clientDataForm').on('submit', function(event) {
        if (!validateForm()) {
            event.preventDefault();
        }
    });
}

function setupCepLookup() {
    $('#cep').blur(function(){
        var cep = $(this).val().replace(/\D/g, '');
        if (cep.length == 8) {
            $.getJSON('https://viacep.com.br/ws/' + cep + '/json/', function(data) {
                if (!("erro" in data)) {
                    $('#logradouro').val(data.logradouro);
                    $('#bairro').val(data.bairro);
                    $('#cidade').val(data.localidade);
                    $('#uf').val(data.uf);
                    $('#ibge').val(data.ibge);
                    $('#numero').focus();
                } else {
                    alert("CEP não encontrado.");
                }
            });
        }
    });
}

function setupCnpjLookup() {
    $('#cnpj').blur(function(){
        var cnpj = $(this).val().replace(/\D/g, '');
        console.log('CNPJ digitado:', cnpj);
        if (cnpj.length == 14) {
            $.ajax({
                url: '/get_empresa_data/',  // Certifique-se de que esta URL está correta
                type: 'GET',
                data: {cnpj: cnpj},
                success: function(data) {
                    console.log('Dados recebidos:', data);
                    if (data.success) {
                        $('#razaoSocial').val(data.razao_social);
                        $('#nomeFantasia').val(data.nome_fantasia);
                        $('#cep').val(data.cep).trigger('blur');
                    } else {
                        alert("Não foi possível encontrar os dados da empresa.");
                    }
                },
                error: function(jqXHR, textStatus, errorThrown) {
                    console.error('Erro na requisição:', textStatus, errorThrown);
                    alert("Erro ao buscar dados da empresa. Por favor, preencha manualmente.");
                }
            });
        }
    });
}

function validateForm() {
    var isValid = true;
    $('[required]').each(function() {
        if ($(this).val() === '') {
            alert(`Por favor, preencha o campo ${$(this).attr('name')}.`);
            isValid = false;
            return false;  // breaks the each() loop
        }
    });
    return isValid;
}

function nextSection(nextSectionId) {
    const currentSection = document.querySelector('div:not(.hidden)');
    currentSection.classList.add('hidden');
    document.getElementById(nextSectionId).classList.remove('hidden');
    updateProgressBar();
}

function prevSection(prevSectionId) {
    const currentSection = document.querySelector('div:not(.hidden)');
    currentSection.classList.add('hidden');
    document.getElementById(prevSectionId).classList.remove('hidden');
    updateProgressBar();
}

function updateProgressBar() {
    const totalSections = 2;
    const currentSectionIndex = Array.from(document.querySelectorAll('div[id$="Section"]')).findIndex(section => !section.classList.contains('hidden')) + 1;
    const progress = (currentSectionIndex / totalSections) * 100;
    document.getElementById('progressBar').style.width = `${progress}%`;
}

// Remove or comment out any calls to bootstrapMaterialDesign() in this file
