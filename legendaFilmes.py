import os
import subprocess
from pathlib import Path
import json
import time
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

# Inicializa o console rich
console = Console()


def get_video_resolution(video_path):
    """
    Obtém a resolução do vídeo usando FFmpeg.
    """
    with console.status(
        "[bold yellow]Analisando resolução do vídeo...", spinner="dots"
    ):
        cmd = ["ffmpeg", "-i", str(video_path)]

        try:
            result = subprocess.run(cmd, stderr=subprocess.PIPE, text=True)
            resolution_match = re.search(r"Stream.*Video:.* (\d+)x(\d+)", result.stderr)

            if resolution_match:
                width = int(resolution_match.group(1))
                height = int(resolution_match.group(2))
                return width, height
            return None
        except Exception as e:
            console.print(f"[bold red]Erro ao obter resolução do vídeo:[/] {str(e)}")
            return None


def get_video_duration(video_path):
    """
    Obtém a duração do vídeo em segundos usando FFmpeg.
    """
    with console.status("[bold yellow]Analisando duração do vídeo...", spinner="dots"):
        cmd = ["ffmpeg", "-i", str(video_path)]

        try:
            result = subprocess.run(cmd, stderr=subprocess.PIPE, text=True)
            duration_match = re.search(
                r"Duration: (\d{2}):(\d{2}):(\d{2})\.(\d{2})", result.stderr
            )

            if duration_match:
                hours = int(duration_match.group(1))
                minutes = int(duration_match.group(2))
                seconds = int(duration_match.group(3))

                total_seconds = hours * 3600 + minutes * 60 + seconds
                return total_seconds
            return None
        except Exception as e:
            console.print(f"[bold red]Erro ao obter duração do vídeo:[/] {str(e)}")
            return None


def parse_time(time_str):
    """
    Converte string de tempo do FFmpeg para segundos.
    """
    time_match = re.search(r"(\d{2}):(\d{2}):(\d{2})\.(\d{2})", time_str)
    if time_match:
        hours = int(time_match.group(1))
        minutes = int(time_match.group(2))
        seconds = int(time_match.group(3))
        return hours * 3600 + minutes * 60 + seconds
    return 0


def format_time(seconds):
    """
    Formata segundos para HH:MM:SS
    """
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    seconds = seconds % 60
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}"


def find_video_and_subtitle(folder):
    """
    Encontra o arquivo de vídeo e legenda em uma pasta.
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
        if file_lower.endswith(video_extensions):
            video_file = file
            table.add_row("Vídeo", str(file))
        elif file_lower.endswith(subtitle_extensions):
            subtitle_file = file
            table.add_row("Legenda", str(file))

    console.print(table)

    if not video_file or not subtitle_file:
        console.print("[bold red]⚠️ Aviso:[/] Vídeo ou legenda não encontrados!")

    return video_file, subtitle_file


def get_appropriate_logo(height):
    """
    Determina qual versão da logo usar baseado na altura do vídeo.
    """
    logos = {720: "720 overlay.png", 1080: "1080 overlay.png"}

    # Encontra a resolução mais próxima
    closest_resolution = min(logos.keys(), key=lambda x: abs(x - height))
    return logos[closest_resolution]


def burn_subtitle_and_logo(input_folder, output_folder):
    """
    Queima a legenda e a logo no vídeo usando FFmpeg.
    """
    video_file, subtitle_file = find_video_and_subtitle(input_folder)

    if not video_file or not subtitle_file:
        console.print(
            f"[bold red]❌ Erro:[/] Vídeo ou legenda não encontrados em {input_folder}"
        )
        return False

    output_folder = Path(output_folder)
    output_folder.mkdir(parents=True, exist_ok=True)

    output_name = f"{video_file.stem}_legendado{video_file.suffix}"
    output_path = output_folder / output_name

    if output_path.exists() and output_path.stat().st_size == video_file.stat().st_size:
        console.print(f"[bold green]✓ Arquivo já existe:[/] {output_path}")
        return True

    # Obtém a resolução do vídeo
    resolution = get_video_resolution(video_file)
    if not resolution:
        console.print(
            "[bold red]❌ Erro:[/] Não foi possível determinar a resolução do vídeo."
        )
        return False

    width, height = resolution
    logo_file = get_appropriate_logo(height)

    # Verifica se o arquivo da logo existe
    logo_path = Path(logo_file)
    if not logo_path.exists():
        console.print(
            f"[bold red]❌ Erro:[/] Arquivo de logo não encontrado: {logo_file}"
        )
        return False

    # Obtém a duração total do vídeo
    total_duration = get_video_duration(video_file)
    if not total_duration:
        console.print(
            "[bold yellow]⚠️ Aviso:[/] Não foi possível determinar a duração do vídeo."
        )
        total_duration = 100

    # Constrói o comando FFmpeg com legenda e logo
    subtitle_path = str(subtitle_file).replace("\\", "/").replace(":", "\\:")
    filter_complex = (
        f"subtitles='{subtitle_path}':force_style='Fontsize=20'[sub];"
        f"[sub][1]overlay=W-w:0[out]"
    )

    command = [
        "ffmpeg",
        "-i",
        str(video_file),
        "-i",
        str(logo_path),
        "-filter_complex",
        filter_complex,
        "-map",
        "[out]",
        "-map",
        "0:a",
        "-c:v",
        "libx264",
        "-preset",
        "faster",
        "-crf",
        "18",
        "-c:a",
        "copy",
        "-y",
        str(output_path),
    ]

    # Mostra o comando em um painel syntax-highlighted
    command_str = " ".join(command)
    syntax = Syntax(command_str, "bash", theme="monokai", word_wrap=True)
    console.print(Panel(syntax, title="[bold]Comando FFmpeg", border_style="blue"))

    try:
        # Configura a barra de progresso rica
        progress = Progress(
            SpinnerColumn(),
            TextColumn("[bold blue]{task.description}"),
            BarColumn(complete_style="green", finished_style="green"),
            TaskProgressColumn(),
            TimeRemainingColumn(),
            console=console,
        )

        process = subprocess.Popen(
            command, stderr=subprocess.PIPE, universal_newlines=True
        )

        with progress:
            task = progress.add_task(f"[cyan]Processando {video_file.name}", total=100)

            last_percent = 0
            while process.poll() is None:
                line = process.stderr.readline()
                if line:
                    time_match = re.search(r"time=(\d{2}:\d{2}:\d{2}\.\d{2})", line)
                    if time_match:
                        current_time = parse_time(time_match.group(1))
                        percent = min(int((current_time / total_duration) * 100), 100)

                        if percent > last_percent:
                            progress.update(task, completed=percent)
                            last_percent = percent

        if process.returncode == 0:
            console.print(
                f"[bold green]✓ Legenda e logo adicionadas com sucesso:[/] {output_path}"
            )
            return True
        else:
            console.print("[bold red]❌ Erro ao processar o vídeo.")
            return False

    except Exception as e:
        console.print(f"[bold red]❌ Erro ao processar {video_file}:[/] {str(e)}")
        return False


# Atualiza a função process_all_folders para usar a nova função
def process_all_folders(base_folder, output_base):
    """
    Processa todas as pastas dentro da pasta base.
    """
    base_path = Path(base_folder)
    output_base_path = Path(output_base)

    folders = [f for f in base_path.iterdir() if f.is_dir()]

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
            console.print(
                f"\n[bold cyan]Processando {i}/{len(folders)}: {folder_path.name}"
            )
            burn_subtitle_and_logo(
                folder_path, output_folder=output_base_path / folder_path.name
            )
    except KeyboardInterrupt:
        console.print("\n[bold red]⚠️ Processamento interrompido pelo usuário.")
        return
    except Exception as e:
        console.print(f"[bold red]❌ Erro inesperado:[/] {e}")
        raise
    finally:
        console.rule("[bold green]Processamento concluído")


if __name__ == "__main__":
    # Configuração de cores e estilos do console
    console = Console()

    # Banner inicial
    console.print(
        Panel.fit(
            "[bold cyan]🎬 Processador de Legendas[/]\n"
            "[italic]Adiciona legendas e logo permanentemente aos seus vídeos[/]",
            border_style="cyan",
        )
    )

    base_folder = "C:/Users/elian/Downloads/FILMES"
    output_base = "C:/Users/elian/Vídeos/FILMES"

    process_all_folders(base_folder, output_base)
