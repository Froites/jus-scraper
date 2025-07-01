CONFIGURE_SEARCH_FORM = """
// Configure dates
document.getElementsByName('dadosConsulta.dtInicio')[0].value = '13/11/2024';
document.getElementsByName('dadosConsulta.dtFim')[0].value = '13/11/2024';

// Configure caderno
var select = document.getElementsByName('dadosConsulta.cdCaderno')[0];
for(var i = 0; i < select.options.length; i++) {
    if(select.options[i].text.includes('caderno 3') && 
       select.options[i].text.includes('Capital - Parte I')) {
        select.selectedIndex = i;
        break;
    }
}

// Configure search keywords
document.getElementsByName('dadosConsulta.pesquisaLivre')[0].value = '"RPV" e "pagamento pelo INSS"';

return 'Form configured successfully';
"""

SCROLL_TO_BOTTOM = "window.scrollTo(0, document.body.scrollHeight);"

OPEN_LINK_IN_NEW_TAB = "window.open(arguments[0], '_blank');"