const exame = document.getElementById("exame");
const consulta = document.getElementById("consulta");
let clicado_exame = false;
let clicado_consulta = false;

exame.addEventListener("mouseenter", function() {
  this.style.backgroundColor = "#F7F9F9";
  this.style.color = "#16C694";
  this.style.border = "1px solid #16C694";
});

exame.addEventListener("mouseleave", function() {
  if (!clicado_exame) {
    this.style.backgroundColor = "#F7F9F9";
    this.style.border = "1px solid #4D4D4D";
    this.style.color = "#4D4D4D";
  }
});

consulta.addEventListener("mouseenter", function() {
  this.style.backgroundColor = "#F7F9F9";
  this.style.color = "#16C694";
  this.style.border = "1px solid #16C694";
});

consulta.addEventListener("mouseleave", function() {
  if (!clicado_consulta) {
    this.style.backgroundColor = "#F7F9F9";
    this.style.border = "1px solid #4D4D4D";
    this.style.color = "#4D4D4D";
  }
});

exame.addEventListener("click", function() {
  clicado_exame = true;
  this.style.backgroundColor = "#F7F9F9";
  this.style.color = "#16C694";
  this.style.border = "1px solid #16C694";

  consulta.style.backgroundColor = "#F7F9F9";
  consulta.style.border = "1px solid #4D4D4D";
  consulta.style.color = "#4D4D4D";

});


consulta.addEventListener("click", function() {
    clicado_consulta = true;
    this.style.backgroundColor = "#F7F9F9";
    this.style.color = "#16C694";
    this.style.border = "1px solid #16C694";
    exame.style.backgroundColor = "#F7F9F9";
    exame.style.border = "1px solid #4D4D4D";
    exame.style.color = "#4D4D4D";
  });



  $(document).ready(function() {
    
    $('#search-box').on('input', function() {
      var query = $(this).val();
      if (query === '') {
        $('#suggestions').empty();
        return;
      }
      if(!clicado_exame && !clicado_consulta){
        alert("Por favor, escolha uma categoria primeiro")
        
      }
      // fazer uma requisição à API ou carregar os dados de um arquivo JSON
      // e retornar uma lista de sugestões que correspondem à consulta
      var suggestions = getSearchSuggestions(query);
      console.log(suggestions)
  
      // limpar a lista de sugestões
      $('#suggestions').empty();
  
      // adicionar cada sugestão à lista
      suggestions.forEach(function(suggestion) {
        $('<li>').text(suggestion).click(function() {
          $('#search-box').val(suggestion); // preencher o input com a sugestão escolhida
          $('#suggestions').empty(); // limpar a lista de sugestões
        }).appendTo('#suggestions');
      });
    });
  
    function getSearchSuggestions(query) {
      // aqui você pode fazer a requisição à API ou carregar os dados de um arquivo JSON
      // e retornar uma lista de sugestões que correspondem à consulta
      return [
        "RESSONÂNCIA MAGNÉTICA - Crânio (encéfalo)",
        "RESSONÂNCIA MAGNÉTICA - Sela túrcica (hipófise)",
        "RESSONÂNCIA MAGNÉTICA - Base do crânio",
        "Estudo funcional (mapeamento cortical por RESSONÂNCIA MAGNÉTICA)",
        "Perfusão cerebral por RESSONÂNCIA MAGNÉTICA",
        "Espectroscopia por RESSONÂNCIA MAGNÉTICA",
        "RESSONÂNCIA MAGNÉTICA - Órbita bilateral",
        "RESSONÂNCIA MAGNÉTICA - Ossos temporais bilateral",
        "RESSONÂNCIA MAGNÉTICA - Face (inclui seios da face)",
        "RESSONÂNCIA MAGNÉTICA - Articulação temporomandibular (bilateral)",
        "RESSONÂNCIA MAGNÉTICA - Pescoço (nasofaringe, orofaringe, laringe, traquéia, tireóide, paratireóide)",
        "RESSONÂNCIA MAGNÉTICA - Tórax (mediastino, pulmão, parede torácica)",
        "RESSONÂNCIA MAGNÉTICA - Coração - morfológico e funcional",
        "RESSONÂNCIA MAGNÉTICA - Coração - morfológico e funcional + perfusão + estresse",
        "RESSONÂNCIA MAGNÉTICA - Coração - morfológico e funcional + perfusão + viabilidade miocárdica",
        'Exame de sangue',
        'Raio-X',
        'Tomografia',
        'Ressonância magnética',
        'Exame de urina',
        'Ecografia'
      ].filter(function(suggestion) {
        return suggestion.toLowerCase().indexOf(query.toLowerCase()) !== -1;
      });
    }

    $('#search-cidade').on('input', function() {
      var query = $(this).val();
      if (query === '') {
        $('#suggestions-cidade').empty();
        return;
      }
      if(!clicado_exame && !clicado_consulta){
        alert("Por favor, escolha uma categoria primeiro")
        
      }
      // fazer uma requisição à API ou carregar os dados de um arquivo JSON
      // e retornar uma lista de sugestões que correspondem à consulta
      var suggestionsCidade = getSearchSuggestionsCidade(query);
    
      // limpar a lista de sugestões
      $('#suggestions-cidade').empty();
    
      // adicionar cada sugestão à lista
      suggestionsCidade.forEach(function(suggestion) {
        $('<li>').text(suggestion).click(function() {
          $('#search-cidade').val(suggestion); // preencher o input com a sugestão escolhida
          $('#suggestions-cidade').empty(); // limpar a lista de sugestões
        }).appendTo('#suggestions-cidade');
      });
    });
    
    function getSearchSuggestionsCidade(query) {
      // aqui você pode fazer a requisição à API ou carregar os dados de um arquivo JSON
      // e retornar uma lista de sugestões que correspondem à consulta
      return [
        'São Paulo, SP',
        'Rio de Janeiro, RJ',
        'Belo Horizonte, MG',
        'Brasília, DF',
        'Salvador, BA',
        'Fortaleza, CE'
      ].filter(function(suggestion) {
        return suggestion.toLowerCase().indexOf(query.toLowerCase()) !== -1;
      });
    }
    
  });



  $('form').on('submit', function(e) {
    e.preventDefault(); // previne o envio padrão do formulário
  
    // Verifica se o usuário escolheu uma categoria
    if (!clicado_exame && !clicado_consulta) {
      alert("Por favor, escolha uma categoria primeiro");
      return;
    }
    // Aqui você pode adicionar outras verificações e validações do formulário, se necessário.
    // Redireciona o usuário para a página desejada
    window.location.href = '/busca';
  });
  



