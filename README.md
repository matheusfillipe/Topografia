# GeoRoad
## Descrição


Plugin para qgis 3.x que possibilita o desenvolvimento do projeto geométrico de estradas. Permite a realização do traçado a partir de diretrizes sore o mapa com imagens de satélite e realiza cálculos de curvas horizontais, verticais e volumes de corte e aterro.

Permite a extração dos resultados por meio de layers (Shapefile ou Geopackage), cad (.dxf), planilha (.csv) e imagens (.png)

A principal objetivo desse plugin é fornecer uma plataforma livre e open source, aliada às funções já existentes no QGIS, como uma alternativa à softwares como o Topograph da Bentley, para o estudo da disciplina de projeto geométrico de estradas. Os dados gerados por esse software ainda não foram completamente validados e não são confiáveis para aplicações em situações reais.

Este plugin funciona para Windows, Mac e Linux, com suas principais funções tendo como única dependência o QGIS instalado no sistema operacional.

---------------------------------------------------------------------

This plugins has the goal to easy the study and apply the process of the geometric road design and comes with the standard Brazilian guidelines for speed limitations, allowed inclinations, curves radius and length.

The basic workflow of this software would be creating a table of segmented points from a vector layer with progressive distance; creating horizontal curves that can be spiral or circular (Segmented); calculating elevations over it from a raster layer; defining the longitudinal profile with parabolic transition curves curves; computing the intersection between the horizontal and vertical data; computing the perpendicular cross section from a raster layer, setting up the road section over the terrain; computing volume and displaying Bruckner's diagram.

Vertical data can be set and edited with a pyqtgraph interface. The cross section setup and volume computations are computing intensive and its recomended 8 GB of ram or more. Most tables can be exported or imported in the formats *.csv for tables and *.dxf.

### Dependências

A partir da versão 1.1 a biblioteca PyOpenGL é requerida. O plugin tentará a instalar automaticamente, mas caso isso falhar, abra o OSGeo4W Shell da pasta de atalhos Qgis e entre com:

```bash
py3_env
python -m pip install PyOpenGL PyOpenGL_accelerate
```

Se tiver algum erro do tipo: "PermissionError: [WinError 5] Access is denied", tente abrir o OsGeo Shell come administrador.

Para que a instalação automática funcione, basta executar o qgis como administrador e instalar o plugin. 

Para Linux e OSX, use o seguinte:

```bash
#Se tiver somente o python3 no sistema:
pip install PyOpenGL PyOpenGL_accelerate


#Se tiver python 2 e 3 juntos:
pip3 install PyOpenGL PyOpenGL_accelerate
```

## Recursos

### Concluídos

* GUI basica e funcionalidades básicas para desenho
* Geração da tabela Horizontal
* Cálculo de curvas horizontais
* Interface para traçado greide (perfil vertical)
* Cálculo de curvas verticais
* Geração da tabela Vertical
* Geração dos perfis transversais a partir de uma seção tipo
* Cálculo de Volumes
* Diagrama de Bruckner
* Extração dos dados em CSV e DXF
* Extração de Modelo tridimensional


### Planejados
* Melhor suporte à layers com fonte Angular (ex: WGS 64)
* Superlargura e Superelevação automáticos
* Cotas a partir de arquivo de pontos cotados(dxf)
* Extração DXF mais detalhada
* Suporte a multithreading e cancelamento de tarefas.

### Como Instalar

#### Instalação Ideal

Procure pelo nome GeoRoad no repositório oficial do Qgis (Plugins -> Intalar plugins) e clique em instalar. 

No momento isso pode ainda não ser possivel.

#### Instalação Manual

1. Baixe o arquivo GeoRoad.zip na página de [releases](https://github.com/matheusfillipe/Topografia/releases) ou nesse [link](https://github.com/matheusfillipe/Topografia/releases/download/v1.1/GeoRoad.zip) 

2. Abra o qgis 3, entre no menu Plugins->Manage and Install Plugins->Install From Zip File

3. Na linha zip file, clique no botão "..." e escolha o arquivo zip do plugin. 

#### Instalação "Forçada"

Coloque a estes arquivos dentro da pasta GeoRoad ou crie essa pasta, no caminho:
 
Linux: ~/.qgis/plugins/python/

Windows:  C:\Users\USER\AppData\Roaming\QGIS\QGIS3\profiles\default\python\plugins

onde USER é seu nome de usuário


## Uso

Um tutorial simplificado de como usar esse complemento: [Wiki](https://github.com/matheusfillipe/Topografia/wiki)


## Reportar erros ou bugs

Caso você queira reportar algum erro não se esqueça de:

1. Caso haja uma janela de erro python, copie todo o conteúdo dela

2. Verifique no painel de logs do qgis, que pode ser acessado no canto inferior direito do programa, as abas python error e GeoRoad e copie todos os logs que existirem lá.

3. Informe exatamente os passos que você fez e verifique se o erro continua acontecendo se você reiniciar o plugin, reinstalar, fechar abrir, etc... 

4. Diga o que aconteceu e o que você esperava acontecer.

5. Envie seu arquivo de projeto (zip e qgis) e layers.

## QGIS

QGIS (anteriormente conhecido como Quantum GIS) é um software livre com código-fonte aberto, multiplataforma de sistema de informação geográfica (SIG) que permite a visualização, edição e análise de dados georreferenciados.

[Download](https://www.qgis.org/pt_BR/site/forusers/download.html#windows) - Qgis 3 for Windows 64 bits

[Download](https://qgis.org/en/site/forusers/alldownloads.html#debian-ubuntu) - Qgis 3 for Linux Debian 

[Download](https://qgis.org/en/site/forusers/download.html) - Other Downloads

## Links and Resources
[Qgis](https://www.qgis.org) - A Free and Open Source Geographic Information System 

[Python3](https://www.python.org/) - Python is a programming language that lets you work quickly
and integrate systems more effectively

#### Documentação:

[Python3](https://www.python.org/)

[Qgis 3.x python API](https://qgis.org/pyqgis/master/)

[Qgis C++ API ](https://qgis.org/api/)

[PyQGIS developer cookbook: Release testing](https://docs.qgis.org/3.4/pdf/en/QGIS-testing-PyQGISDeveloperCookbook-en.pdf)

[Qt5 API](https://doc.qt.io/qt-5)

[PyQtGraph](http://www.pyqtgraph.org/) --> A versão utilizada nesse plugin está modificada!


<br>


## Licença

### GPL 2
<br>
This program is free software; you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation; either version 2 of the License, or (at your option) any later version.                                   




