# Análise do Fluxo de Execução - Processador de Vídeo

## Cenário de Teste
Vamos simular o processamento de um vídeo com os seguintes parâmetros:
- Pasta de entrada: `/videos/episodio1/`
- Arquivo de vídeo: `episodio1.mp4`
- Arquivo de legenda: `episodio1.srt`
- Resolução do vídeo: 1920x1080
- Duração: 30 minutos (1800 segundos)

## 1. Entrada no Sistema
```python
burn_subtitle_and_logo("/videos/episodio1/", "/videos/output/episodio1/")
```

## 2. Verificação Inicial de Arquivos
### 2.1 Execução de `find_video_and_subtitle()`
- Entrada na pasta `/videos/episodio1/`
- Busca por extensões definidas em VIDEO_EXTENSIONS e SUBTITLE_EXTENSIONS
- Resultado:
  - video_file = Path("/videos/episodio1/episodio1.mp4")
  - subtitle_file = Path("/videos/episodio1/episodio1.srt")

### 2.2 Verificação com `should_process_video()`
- Verifica existência de arquivos "_legendado.mp4" ou "_logo.mp4"
- Resultado: True, None (deve processar, nenhuma mensagem de erro)

## 3. Análise do Vídeo
### 3.1 Execução de `get_video_metadata()`
```python
metadata = {
    "resolution": (1920, 1080),
    "duration": 1800
}
```

## 4. Processamento da Legenda
### 4.1 Execução de `convert_subtitle_to_utf8()`
- Tenta leitura com diferentes encodings
- Resultado: Path("/videos/episodio1/episodio1_utf8.srt")

## 5. Seleção da Logo
### 5.1 Execução de `get_appropriate_logo()`
- Altura do vídeo: 1080
- Resultado: Path("/assets/1080 overlay.png")

## 6. Construção do Comando FFmpeg
### 6.1 Configurações de Vídeo
```python
video_options = [
    "-c:v", "libx264",
    "-preset", "medium",
    "-crf", "23",
    # ... outras opções
]
```

### 6.2 Configurações de Áudio
```python
audio_options = [
    "-c:a", "aac",
    "-b:a", "128k",
    "-ar", "44100",
    "-ac", "2"
]
```

### 6.3 Comando FFmpeg Final
```bash
ffmpeg -i episodio1.mp4 -i 1080overlay.png -f mp4 -filter_complex \
    "subtitles='episodio1_utf8.srt',overlay=W-w:0" \
    [opções de vídeo e áudio] \
    -y /videos/output/episodio1/episodio1_legendado.mp4
```

## 7. Execução e Monitoramento
### 7.1 Progress Bar
- Início: 0%
- Monitoramento através de regex: "time=(\d{2}:\d{2}):(\d{2}\.\d{2})"
- Atualização progressiva até 100%

### 7.2 Finalização
- Cálculo de redução de tamanho:
  ```python
  input_size = tamanho_original
  output_size = tamanho_final
  reduction = ((input_size - output_size) / input_size) * 100
  ```

## Pontos de Verificação e Possíveis Erros

### Verificações Críticas:
1. **Entrada de Arquivos**
   - ✓ Existência do vídeo
   - ✓ Formato do vídeo suportado
   - ✓ Existência da legenda (opcional)

2. **Metadados do Vídeo**
   - ✓ Resolução válida
   - ✓ Duração detectada

3. **Processamento de Legenda**
   - ✓ Codificação detectada
   - ✓ Conversão para UTF-8 bem-sucedida

4. **Logo**
   - ✓ Arquivo existe
   - ✓ Resolução apropriada selecionada

### Possíveis Pontos de Falha:
1. FFmpeg não instalado ou inacessível
2. Permissões de arquivo insuficientes
3. Espaço em disco insuficiente
4. Legenda mal formatada
5. Codificação da legenda não detectada
6. Arquivo de logo ausente para a resolução necessária
7. Erro durante o processamento do FFmpeg

## Saídas Esperadas

### Sucesso:
```
✓ Processamento concluído com sucesso: /videos/output/episodio1/episodio1_legendado.mp4
📊 Redução de tamanho: XX.X%
```

### Erro:
```
❌ Erro: [Mensagem específica do erro]
```