# 🎬 Processador de Legendas e Logo

Um script Python robusto para adicionar legendas e logos permanentemente em vídeos usando FFmpeg, com uma interface de linha de comando rica e intuitiva.

## 📋 Características

- ✨ Interface de usuário rica e informativa usando `rich`
- 🎯 Detecção automática de arquivos de vídeo e legendas
- 🖼️ Suporte a diferentes resoluções de vídeo (720p, 1080p)
- 📊 Barra de progresso em tempo real
- 🔄 Processamento em lote de múltiplas pastas
- 🎨 Logo adaptativa baseada na resolução do vídeo
- ⚡ Otimizado para qualidade e desempenho

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

1. Organize seus vídeos em pastas individuais com suas respectivas legendas
2. Coloque os arquivos de logo (`720 overlay.png` e `1080 overlay.png`) no mesmo diretório do script
3. Ajuste as pastas de entrada e saída no script:
   ```python
   base_folder = "C:/caminho/para/pasta/entrada"
   output_base = "C:/caminho/para/pasta/saida"
   ```
4. Execute o script:
   ```bash
   python video_processor.py
   ```

## 📁 Estrutura de Arquivos Esperada

```
pasta_base/
├── filme1/
│   ├── video.mp4
│   └── legenda.srt
├── filme2/
│   ├── video.mkv
│   └── legenda.srt
└── ...
```

## 🎯 Formatos Suportados

- **Vídeos**: .mp4, .mkv, .avi
- **Legendas**: .srt, .ass, .ssa
- **Logos**: .png (720p e 1080p)

## ⚙️ Configurações do FFmpeg

O script utiliza as seguintes configurações para processamento:
- Codec de vídeo: libx264
- Preset: faster
- CRF: 18
- Áudio: cópia direta do original

## 🔍 Funcionalidades Detalhadas

- **Detecção Automática de Resolução**: Identifica a resolução do vídeo e aplica a logo apropriada
- **Verificação de Arquivos**: Valida a presença de vídeos e legendas antes do processamento
- **Interface Rica**: Usa tabelas coloridas e painéis informativos para melhor visualização
- **Monitoramento de Progresso**: Exibe barra de progresso com tempo estimado
- **Tratamento de Erros**: Manipulação robusta de erros com mensagens claras

## ⚠️ Observações Importantes

1. O script não sobrescreve arquivos existentes de mesmo tamanho
2. As logos devem estar nomeadas como "720 overlay.png" e "1080 overlay.png"
3. O processo pode ser interrompido com Ctrl+C
4. É necessário ter permissões de leitura/escrita nas pastas

## 🐛 Resolução de Problemas

Se encontrar problemas:

1. Verifique se o FFmpeg está instalado corretamente
2. Confirme as permissões das pastas
3. Verifique se os arquivos de logo existem
4. Certifique-se de que os formatos dos arquivos são suportados

## 🤝 Contribuindo

Contribuições são bem-vindas! Por favor:

1. Faça um Fork do projeto
2. Crie uma branch para sua feature
3. Faça commit das mudanças
4. Envie um Pull Request

## 📄 Licença

Este projeto está sob a licença MIT. Veja o arquivo `LICENSE` para mais detalhes.
