from jinja2 import Template

def processar_template(template, variaveis):
    try:
        #Converter a template para usar a sintaxe Jinja2
        template_jinja = template
        
        #Se as templates usam {NOME} em vez de {{nome}}, fazer a conversão
        for chave in variaveis.keys():
            padrao_antigo = '{' + chave.upper() + '}'
            padrao_jinja = '{{ ' + chave + ' }}'
            template_jinja = template_jinja.replace(padrao_antigo, padrao_jinja)
            
        #Processar a template com o Jinja2
        template_processado = Template(template_jinja).render(**variaveis)
        return template_processado
    except Exception as e:
        print(f"Erro ao processar a template: {e}")
        return None