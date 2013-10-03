Novo FlexA - Um Novo Sistema de Arquivos Flexível e Adaptável
==============================================================

Introdução
----------
O Novo FlexA é uma reescrita do FlexA [1], um sistema de arquivos flexível e
adaptável desenvolvido no Grupo de Sistemas Distribuídos e Adaptável (GSPD)
[2] da UNESP, no instituto de Biociências, Letras e Ciências Exatas (IBILCE),
localizado em São José do Rio Preto.

A versão original do FlexA tem como autores:

1. Silas Evandro Nachif Fernandes
2. Danilo Costa Marim Segura
3. Matheus Della Croce Oliveira
4. Leandro Moreira Barbosa
5. Lúcio Rodrigo de Carvalho
6. Thiago Kenji Okada

O FlexA original é um sistema de arquivos disitribuído rodando em espaço de
usuário e escrito na linguagem de programação Python 2. Para mais detalhes
sobre o sistema de arquivos em si, recomenda-se ler a monografia do Silas [1]
assim como outras publicações geradas a partir do desenvolvimento desse
sistema de arquivos [3].

Infelizmente, o código original desse sistema estava um caos, e a correria
para terminar os trabalhos tornou o código ainda pior. A ideia de reescrita
do código vem de longa data e só agora rendeu alguns frutos.

Objetivos
---------
O objetivo dessa reescrita é tornar o código do FlexA mais organizado e
estruturado, de maneira que facilite o entendimento do código e o
desenvolvimento de novas funções. Além disso, a documentação será feita em
cada módulo criado, tornando a vida dos futuros desenvolvedores do sistema
mais simples.

Para isso, um dos objetivos é tentar seguir o PEP 8 [4], que fala sobre um
guia de estilos para o Python, ao máximo. Com o objetivo de manter uma boa
documentação, é importante que cada função/classe/etc. seja documentada
usando  docstrings. Uma boa introdução sobre docstrings, assim como uma
convenção de como usá-las para manter um padrão pode ser encontrada no
PEP 257 [5].

Lembrando que ao usar o docstrings a geração de documentação do código pode
ser automatizada, além de permitir um desenvolvimento mais rápido de código
com o uso de funções como o help() do Python. Ou seja, boa documentação gera
mais código (bom), e não o contrário.

Dependências
------------
O código por enquanto depende da biblioteca pycrypto para encriptação.

Observações
-----------
O código atualmente se encontra usando o interpretador Python 2, que está no
fim de sua vida (EOL: end of life) [6]. O antigo FlexA não tinha nenhuma
dependência que não tivesse port para a versão 3 do Python, porém existiam
muitas partes do código incompatíveis com a nova versão (e o código em si foi
desenvolvido sem se importar muito com a compatibilidade).

Estamos fazendo um esforço para rodar o Novo FlexA no Python 3, mas isso deve
ser entendido como apenas isso: um esforço. Evitando usar a versão antiga do
comando 'print' (no Python 3, o print é uma função) ou sempre fazer conversão
explícita entre variáveis ajuda a garantir que o código atual rode no Python
3, porém novas dependências podem ser introduzidas no código que o tornem
apenas compatível com a versão mais antiga do Python.

[1]: http://www.dcce.ibilce.unesp.br/spd
[2]: http://www.dcce.ibilce.unesp.br/spd/pubs/FlexA_PDPTA.pdf
[3]: http://www.dcce.ibilce.unesp.br/spd/publication.php
[4]: http://www.python.org/dev/peps/pep-0008
[5]: http://www.python.org/dev/peps/pep-0257
[6]: https://wiki.python.org/moin/Python2orPython3
