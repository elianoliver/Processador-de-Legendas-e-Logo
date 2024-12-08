import os
import subprocess
from pathlib import Path
import json
import re
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import (
    Progress,
    TextColumn,
    BarColumn,
    TaskProgressColumn,
    TimeRemainingColumn,
    SpinnerColumn,
)
from rich.syntax import Syntax
from rich import print as rprint
from rich.live import Live

# 1. Inicialização e Configuração (única)
console = Console()

# 2. Funções de Utilidade para Tempo
def parse_time(time_str):
    """
    Converte string de tempo do FFmpeg para segundos incluindo milissegundos.
    """
    time_match = re.search(r"(\d{2}):(\d{2}):(\d{2})\.(\d{2})", time_str)
    if time_match:
        hours = int(time_match.group(1))
        minutes = int(time_match.group(2))
        seconds = int(time_match.group(3))
        milliseconds = int(time_match.group(4)) / 100.0
        return hours * 3600 + minutes * 60 + seconds + milliseconds
    return 0

# 3. Funções de Análise de Vídeo
def get_video_metadata(video_path):
    """
    Obtém todos os metadados relevantes do vídeo em uma única chamada FFmpeg.
    """
    with console.status("[bold yellow]Analisando metadados do vídeo...", spinner="dots"):
        cmd = ["ffmpeg", "-i", str(video_path)]
        try:
            result = subprocess.run(cmd, stderr=subprocess.PIPE, text=True)

            # Extrair resolução
            resolution_match = re.search(r"Stream.*Video:.* (\d+)x(\d+)", result.stderr)
            width = height = None
            if resolution_match:
                width = int(resolution_match.group(1))
                height = int(resolution_match.group(2))

            # Extrair duração
            duration_match = re.search(
                r"Duration: (\d{2}):(\d{2}):(\d{2})\.(\d{2})", result.stderr
            )
            duration = None
            if duration_match:
                hours = int(duration_match.group(1))
                minutes = int(duration_match.group(2))
                seconds = int(duration_match.group(3))
                duration = hours * 3600 + minutes * 60 + seconds

            return {
                "resolution": (width, height) if width and height else None,
                "duration": duration
            }

        except FileNotFoundError:
            console.print("[bold red]Erro:[/] FFmpeg não encontrado no sistema")
            raise
        except Exception as e:
            console.print(f"[bold red]Erro ao obter metadados do vídeo:[/] {str(e)}")
            raise RuntimeError(f"Erro ao processar vídeo: {str(e)}")

def get_appropriate_logo(height, assets_dir=None):
    """
    Determina qual versão da logo usar baseado na altura do vídeo.

    Args:
        height (int): Altura do vídeo em pixels
        assets_dir (Path, optional): Diretório dos assets para teste.
            Se None, usa o diretório padrão.

    Returns:
        Path: Caminho para a logo apropriada

    Raises:
        FileNotFoundError: Se o diretório de assets ou a logo não for encontrada
    """
    if assets_dir is None:
        assets_dir = Path(__file__).parent / "assets"

    if not assets_dir.exists():
        raise FileNotFoundError(f"Diretório de assets não encontrado: {assets_dir}")

    logos = {
        720: assets_dir / "720 overlay.png",
        1080: assets_dir / "1080 overlay.png"
    }

    # Verifica se os arquivos de logo existem
    for resolution, logo_path in logos.items():
        if not logo_path.exists():
            raise FileNotFoundError(f"Arquivo de logo não encontrado: {logo_path}")

    closest_resolution = min(logos.keys(), key=lambda x: abs(x - height))
    return logos[closest_resolution]

# 4. Funções de Busca de Arquivos
def find_video_and_subtitle(folder):
    """
    Encontra o arquivo de vídeo e legenda em uma pasta.
    Otimizado para parar quando encontrar ambos.
    """
    video_extensions = (".mp4", ".mkv", ".avi")
    subtitle_extensions = (".srt", ".ass", ".ssa")

    video_file = None
    subtitle_file = None
    folder_path = Path(folder)

    # Cria uma tabela para mostrar os arquivos encontrados
    table = Table(title=f"\nArquivos em [cyan]{folder_path}[/]")
    table.add_column("Tipo", style="bold magenta")
    table.add_column("Arquivo", style="green")

    for file in folder_path.iterdir():
        file_lower = str(file).lower()
        if file_lower.endswith(video_extensions) and not video_file:
            video_file = file
            table.add_row("Vídeo", str(file))
        elif file_lower.endswith(subtitle_extensions) and not subtitle_file:
            subtitle_file = file
            table.add_row("Legenda", str(file))

        # Para a busca se encontrou ambos
        if video_file and subtitle_file:
            break

    console.print(table)

    if not video_file:
        console.print("[bold red]⚠️ Aviso:[/] Vídeo não encontrado!")
    elif not subtitle_file:
        console.print("[bold yellow]ℹ️ Info:[/] Nenhuma legenda encontrada. Será adicionada apenas a logo.")

    return video_file, subtitle_file

def create_ffmpeg_command(video_file, subtitle_file, logo_file, output_path, video_options, audio_options):
    """
    Cria o comando FFmpeg unificado para processamento.
    """
    if subtitle_file:
        # Comando combinado com legenda e logo em um único passo
        return [
            "ffmpeg",
            "-i", video_file,
            "-i", logo_file,
            "-filter_complex",
            f"subtitles={subtitle_file},overlay=W-w:0",
        ] + video_options + audio_options + [
            "-y", output_path
        ]
    else:
        # Comando apenas com logo
        return [
            "ffmpeg",
            "-i", video_file,
            "-i", logo_file,
            "-filter_complex", "overlay=W-w:0",
        ] + video_options + audio_options + [
            "-y", output_path
        ]

def should_process_video(video_path, output_folder):
    """
    Centraliza todas as verificações necessárias antes do processamento.
    """
    if not video_path:
        return False, "Vídeo não encontrado"

    possible_suffixes = ["_legendado.mp4", "_logo.mp4"]
    for suffix in possible_suffixes:
        output_path = output_folder / f"{video_path.stem}{suffix}"
        if output_path.exists():
            return False, f"Arquivo já processado: {output_path}"

    return True, None

def convert_subtitle_to_utf8(subtitle_path):
    """
    Verifica a codificação da legenda e converte para UTF-8 se necessário.
    """
    # Lista de codificações comuns para testar
    encodings = ['utf-8', 'iso-8859-1', 'windows-1252', 'ansi']

    # Verifica se já existe arquivo UTF-8
    utf8_path = subtitle_path.parent / f"{subtitle_path.stem}_utf8{subtitle_path.suffix}"
    if utf8_path.exists():
        return utf8_path

    # Detecta codificação
    for encoding in encodings:
        try:
            with open(subtitle_path, 'r', encoding=encoding) as f:
                content = f.read()
                if encoding == 'utf-8':
                    return subtitle_path
                break
        except UnicodeDecodeError:
            continue
    else:
        console.print(f"[bold red]❌ Erro:[/] Não foi possível detectar a codificação da legenda")
        return None

    # Cria nova legenda UTF-8
    try:
        with open(utf8_path, 'w', encoding='utf-8') as f:
            f.write(content)
        console.print(f"[bold green]✓ Legenda convertida para UTF-8:[/] {utf8_path}")
        return utf8_path
    except Exception as e:
        console.print(f"[bold red]❌ Erro ao converter legenda para UTF-8:[/] {str(e)}")
        return None

def process_video(progress, task, process, total_duration, start_percent=0, end_percent=100):
    """
    Processa a saída do FFmpeg e atualiza o progresso.

    Args:
        progress: Objeto Progress da rich
        task: ID da tarefa
        process: Processo FFmpeg
        total_duration: Duração total do vídeo
        start_percent: Porcentagem inicial para esta etapa
        end_percent: Porcentagem final para esta etapa
    """
    range_size = end_percent - start_percent

    while process.poll() is None:
        line = process.stderr.readline()
        if line:
            if "Error" in line or "Invalid" in line:
                console.print(f"[yellow]⚠️ FFmpeg:[/] {line.strip()}")

            time_match = re.search(r"time=(\d{2}:\d{2}):(\d{2}\.\d{2})", line)
            if time_match:
                current_time = parse_time(time_match.group(0))
                progress_ratio = min(current_time / total_duration, 1.0)
                current_percent = start_percent + (progress_ratio * range_size)
                progress.update(task, completed=current_percent)

    return process.returncode == 0

def burn_subtitle_and_logo(input_folder, output_folder, assets_dir=None):
    """
    Função principal otimizada para processar o vídeo.
    """
    # Verificações iniciais
    video_file, subtitle_file = find_video_and_subtitle(input_folder)
    should_process, message = should_process_video(video_file, Path(output_folder))
    if not should_process:
        console.print(f"[yellow]⚠️ {message}")
        return False

    # Configurar output
    output_folder = Path(output_folder)
    output_folder.mkdir(parents=True, exist_ok=True)
    output_suffix = "_legendado" if subtitle_file else "_logo"
    output_path = output_folder / f"{video_file.stem}{output_suffix}.mp4"

    # Obter metadados do vídeo
    metadata = get_video_metadata(video_file)
    if not metadata["resolution"]:
        console.print("[bold red]❌ Erro:[/] Não foi possível determinar a resolução do vídeo.")
        return False

    width, height = metadata["resolution"]
    total_duration = metadata["duration"] or 100

    # Processar legenda se existir
    if subtitle_file:
        subtitle_file = convert_subtitle_to_utf8(subtitle_file)
        if not subtitle_file:
            return False

    # Obter logo apropriada
    try:
        logo_file = get_appropriate_logo(height, assets_dir)
    except Exception as e:
        console.print(f"[bold red]❌ Erro ao obter logo:[/] {str(e)}")
        return False

    # Configurações de codificação otimizadas
    video_options = [
        "-c:v", "libx264",
        "-preset", "medium",
        "-crf", "23",
        "-tune", "film",
        "-profile:v", "high",
        "-level", "4.1",
        "-movflags", "+faststart",
        "-x264opts", "me=umh:subme=7:ref=4:b-adapt=2:direct=auto:rc-lookahead=50:deblock=-1,-1:psy-rd=0.8,0.2:aq-mode=3:aq-strength=0.8",
    ]

    audio_options = [
        "-c:a", "aac",
        "-b:a", "128k",
        "-ar", "44100",
        "-ac", "2"
    ]

    # Criar comando FFmpeg unificado
    command = create_ffmpeg_command(
        str(video_file),
        str(subtitle_file) if subtitle_file else None,
        str(logo_file),
        str(output_path),
        video_options,
        audio_options
    )

    # Processar vídeo
    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[bold blue]{task.description}"),
            BarColumn(complete_style="green", finished_style="green"),
            TaskProgressColumn(),
            TimeRemainingColumn(),
            console=console,
        ) as progress:
            task = progress.add_task(
                f"[cyan]Processando {video_file.name}",
                total=100
            )

            process = subprocess.Popen(
                command,
                stderr=subprocess.PIPE,
                stdout=subprocess.PIPE,
                universal_newlines=True
            )

            if not process_video(progress, task, process, total_duration, start_percent=0, end_percent=100):
                raise RuntimeError("Falha ao processar o vídeo")

            # Calcular e mostrar redução de tamanho
            input_size = os.path.getsize(video_file)
            output_size = os.path.getsize(output_path)
            reduction = ((input_size - output_size) / input_size) * 100

            console.print(
                f"[bold green]✓ Processamento concluído com sucesso:[/] {output_path}\n"
                f"[bold blue]📊 Redução de tamanho:[/] {reduction:.1f}%"
            )
            return True

    except Exception as e:
        console.print(f"[bold red]❌ Erro ao processar o vídeo:[/] {str(e)}")
        return False

def process_all_folders(base_folder, output_base):
    """
    Processa todas as pastas dentro da pasta base.
    """
    base_path = Path(base_folder)
    output_base_path = Path(output_base)
    folders = [f for f in base_path.iterdir() if f.is_dir()]

    if not folders:
        console.print("[yellow]⚠️ Nenhuma pasta encontrada para processar.")
        return

    console.print(
        Panel.fit(
            f"[bold green]🎬 Encontradas {len(folders)} pastas para processar[/]\n"
            f"[bold blue]📁 Pasta base:[/] {base_path}\n"
            f"[bold blue]📁 Pasta saída:[/] {output_base_path}",
            title="Resumo do Processamento",
            border_style="cyan",
        )
    )

    try:
        for i, folder_path in enumerate(folders, 1):
            console.print(f"\n[bold cyan]Processando pasta {i}/{len(folders)}: {folder_path.name}")
            output_folder = output_base_path / folder_path.name
            burn_subtitle_and_logo(folder_path, output_folder)

    except KeyboardInterrupt:
        console.print("\n[bold red]⚠️ Processamento interrompido pelo usuário.")
    except Exception as e:
        console.print(f"[bold red]❌ Erro inesperado:[/] {e}")
        raise
    finally:
        console.print("\n[bold green]Processamento concluído")

if __name__ == "__main__":
    script_dir = Path(__file__).parent
    base_folder = script_dir / "input"
    output_base = script_dir / "output"

    console.print(
        Panel.fit(
            "[bold cyan]🎬 Processador de Legendas[/]\n"
            "[italic]Adiciona legendas e logo permanentemente aos seus vídeos[/]",
            border_style="cyan",
        )
    )

    process_all_folders(base_folder, output_base)