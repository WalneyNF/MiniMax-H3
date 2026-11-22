# WMK MiniMax-H3 Lite — V0.1.0

Protótipo independente para computadores simples, destinado à integração futura no fork `WalneyNF/MiniMax-H3`.

## Iniciar no Windows
1. Instale Python 3.10+ e opcionalmente Ollama + FFmpeg. Não exige pip/install nem GPU para iniciar.
2. Extraia o ZIP numa pasta qualquer e execute `INICIAR.bat`.
3. Abra `http://127.0.0.1:8767/`.
4. Crie cenas, mova/redimensione os painéis e salve layouts; os projetos ficam no `localStorage` do navegador e podem ser exportados/importados via JSON.
5. Com Ollama executando, clique em **Diagnosticar** e selecione o modelo local. Gere prompts cinematográficos sem mandar texto a servidores externos.
6. Importe MP4 em uma cena e exporte o filme em 720p (precisa FFmpeg no PATH).

## Limites conhecidos da V0.1
- Não executa o MiniMax-H3; o objetivo é preparar roteiro, cenas e prompts num PC modesto.
- Exportação MP4 **sem faixa de áudio** nesta versão; preservar e misturar áudio será feito depois.
- A montagem MP4 usa FFmpeg e pode demorar em CPU simples. Limite recomendado de clipe: 300 MB cada.
- O upload HTTP da V0.1 é local, sem autenticação, e o servidor só escuta 127.0.0.1.
- Projetos são guardados no navegador (localStorage). Exporte o JSON para fazer backup.
- O formato de prompt segue seções básicas da skill `h3-prompt-writing`; ainda não cobre todos os modos Ref2VA.
- CORS não precisa ser modificado no Ollama: Python chama a API do Ollama do lado do servidor.

## Arquivos
- `index.html`: interface sem frameworks, com painéis arrastáveis, redimensionáveis e presets de layout.
- `server.py`: servidor local, diagnóstico Ollama/FFmpeg, geração de prompt, upload MP4 e renderização.
- `INICIAR.bat`: inicialização no Windows.

## Segurança
Não exponha a porta 8767 na Internet; o servidor não possui login. Não execute arquivos de terceiros como projetos. O aplicativo não transmite seus arquivos para terceiros na V0.1.

Créditos: Walney Moreira Klein — walneyk@hotmail.com