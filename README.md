# 🎬 Processador de Legendas e Logo

Um script Python robusto para adicionar legendas e logos permanentemente em vídeos usando FFmpeg, com uma interface de linha de comando rica e intuitiva.

## 📋 Características

- ✨ Interface de usuário rica e informativa usando `rich`
- 🎯 Detecção automática de arquivos de vídeo e legendas
- 🖼️ Suporte a diferentes resoluções de vídeo (720p, 1080p)
- 📊 Barra de progresso em tempo real
- 🔄 Processamento em lote de múltiplas pastas
- 🎨 Logo adaptativa baseada na resolução do vídeo
- ⚡ Otimizado para eficiência de memória e desempenho
- 🔧 Processamento em duas etapas para evitar problemas de memória

## 🛠️ Pré-requisitos

- Python 3.6+
- FFmpeg instalado e disponível no PATH do sistema
- Bibliotecas Python requeridas:
  ```
  rich
  ```

## 📦 Instalação

1. Clone o repositório ou baixe o código fonte
2. Instale as dependências:
   ```bash
   pip install rich
   ```
3. Certifique-se de que o FFmpeg está instalado:
   ```bash
   ffmpeg -version
   ```

## 🚀 Uso

1. Coloque seus vídeos e legendas na pasta `input` em subpastas próprias
2. Os arquivos de logo (`720 overlay.png` e `1080 overlay.png`) devem estar na pasta `assets`
3. Execute o script:
   ```bash
   python legendaFilmes.py
   ```
4. Os vídeos processados serão salvos na pasta `output` mantendo a mesma estrutura de pastas

## 📁 Estrutura de Arquivos

```
Processador-de-Legendas-e-Logo/
├── input/
│   ├── Filme1/
│   │   ├── video.mp4
│   │   └── legenda.srt
│   └── Filme2/
│       ├── video.mkv
│       └── legenda.srt
├── output/
│   └── (vídeos processados)
├── assets/
│   ├── 720 overlay.png
│   └── 1080 overlay.png
├── modules/
│   ├── __init__.py
│   ├── config.py
│   ├── file_utils.py
│   ├── ffmpeg_utils.py
│   ├── processor.py
│   ├── subtitle_utils.py
│   ├── time_utils.py
│   └── video_analysis.py
└── legendaFilmes.py
```

## 🎯 Formatos Suportados

- **Vídeos**: .mp4, .mkv, .avi
- **Legendas**: .srt, .ass, .ssa
- **Logos**: .png (720p e 1080p)

## ⚙️ Processamento em Duas Etapas

Para otimizar o uso de memória, o script agora processa os vídeos em duas etapas separadas:

1. **Etapa 1**: Adição de legendas ao vídeo original
   - Cria um arquivo temporário intermediário com as legendas embutidas

2. **Etapa 2**: Adição da logo ao vídeo com legendas
   - Processa o arquivo intermediário para adicionar a logo
   - Gera o arquivo final com legendas e logo

3. **Limpeza**: Remove o arquivo temporário intermediário automaticamente

Este método evita problemas de memória que podem ocorrer ao processar vídeos grandes.

## ⚙️ Configurações de Codificação

O script utiliza configurações otimizadas para o FFmpeg:
- Codec de vídeo: libx264
- Preset: medium
- CRF: 26
- Tune: film
- Profile: high
- Movflags: +faststart
- Áudio: cópia direta do original (sem recodificação)

## 🔍 Funcionalidades Detalhadas

- **Detecção Automática de Resolução**: Identifica a resolução do vídeo e aplica a logo apropriada
- **Verificação de Arquivos**: Valida a presença de vídeos e legendas antes do processamento
- **Interface Rica**: Usa tabelas coloridas e painéis informativos para melhor visualização
- **Monitoramento de Progresso**: Exibe barra de progresso com tempo estimado
- **Tratamento de Erros**: Manipulação robusta de erros com mensagens claras
- **Otimização de Memória**: Processamento em etapas para vídeos de grande porte

## ⚠️ Observações Importantes

1. O script não sobrescreve arquivos existentes de mesmo tamanho
2. As logos devem estar nomeadas como "720 overlay.png" e "1080 overlay.png"
3. O processo pode ser interrompido com Ctrl+C
4. O processamento em duas etapas é mais lento, mas usa menos memória

## 🐛 Resolução de Problemas

Se encontrar problemas:

1. Verifique se o FFmpeg está instalado corretamente
2. Confirme as permissões das pastas
3. Verifique se os arquivos de logo existem na pasta `assets`
4. Para problemas de memória, verifique se o processamento em duas etapas está funcionando corretamente
5. Certifique-se de que os formatos dos arquivos são suportados

## 🤝 Contribuindo

Contribuições são bem-vindas! Por favor:

1. Faça um Fork do projeto
2. Crie uma branch para sua feature
3. Faça commit das mudanças
4. Envie um Pull Request

## 📄 Licença

Este projeto está sob a licença MIT. Veja o arquivo `LICENSE` para mais detalhes.
