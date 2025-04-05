# modules/processor.py
import os
import subprocess
import re
from pathlib import Path
from rich.progress import (
    Progress,
    TextColumn,
    BarColumn,
    TaskProgressColumn,
    TimeRemainingColumn,
    SpinnerColumn,
)
from rich.panel import Panel

from .config import console
from .time_utils import parse_time
from .video_analysis import get_video_metadata, get_appropriate_logo
from .file_utils import find_video_and_subtitle, should_process_video
from .subtitle_utils import convert_subtitle_to_utf8
from .ffmpeg_utils import create_ffmpeg_command

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
    Função principal otimizada para processar o vídeo em duas etapas separadas.

    Args:
        input_folder: Pasta contendo o vídeo e legenda
        output_folder: Pasta onde será salvo o vídeo processado
        assets_dir: Diretório opcional contendo as logos
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

    # Cria um arquivo intermediário para a etapa de legendas
    temp_output_path = output_folder / f"{video_file.stem}_legendado_temp.mp4"
    final_output_path = output_folder / f"{video_file.stem}_completo.mp4"

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
        "-crf", "26",
        "-tune", "film",
        "-profile:v", "high",
        "-movflags", "+faststart",
    ]

    # Copia o áudio original sem recodificar
    audio_options = [
        "-c:a", "copy"
    ]

    # Salvar o diretório atual
    original_dir = os.getcwd()

    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[bold blue]{task.description}"),
            BarColumn(complete_style="green", finished_style="green"),
            TaskProgressColumn(),
            TimeRemainingColumn(),
            console=console,
        ) as progress:
            # Mudar para o diretório do vídeo/legenda antes de executar o FFmpeg
            os.chdir(video_file.parent)

            # ETAPA 1: Adicionar legendas
            if subtitle_file:
                task1 = progress.add_task(
                    f"[cyan]Etapa 1/2: Adicionando legendas ao vídeo",
                    total=100
                )

                subtitle_command = [
                    "ffmpeg",
                    "-i", str(video_file),
                    "-vf", f"subtitles='{subtitle_file.name}'",
                ] + video_options + audio_options + [
                    "-y", str(temp_output_path)
                ]

                process1 = subprocess.Popen(
                    subtitle_command,
                    stderr=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    universal_newlines=True
                )

                if not process_video(progress, task1, process1, total_duration):
                    console.print("[bold red]❌ Erro:[/] Falha ao adicionar legendas ao vídeo")
                    return False

                input_for_logo = temp_output_path
            else:
                input_for_logo = video_file

            # ETAPA 2: Adicionar logo
            task2 = progress.add_task(
                f"[cyan]Etapa 2/2: Adicionando logo ao vídeo",
                total=100
            )

            logo_command = [
                "ffmpeg",
                "-i", str(input_for_logo),
                "-i", str(logo_file),
                "-filter_complex", "overlay=W-w:0",
            ] + video_options + audio_options + [
                "-y", str(final_output_path)
            ]

            process2 = subprocess.Popen(
                logo_command,
                stderr=subprocess.PIPE,
                stdout=subprocess.PIPE,
                universal_newlines=True
            )

            if not process_video(progress, task2, process2, total_duration):
                console.print("[bold red]❌ Erro:[/] Falha ao adicionar logo ao vídeo")
                return False

            # Remover arquivo temporário se existir
            if subtitle_file and temp_output_path.exists():
                try:
                    temp_output_path.unlink()
                except:
                    console.print("[yellow]⚠️ Não foi possível remover o arquivo temporário")

            # Calcular e mostrar redução de tamanho
            input_size = os.path.getsize(video_file)
            output_size = os.path.getsize(final_output_path)
            reduction = ((input_size - output_size) / input_size) * 100

            console.print(
                f"[bold green]✓ Processamento concluído com sucesso:[/] {final_output_path}\n"
                f"[bold blue]📊 Redução de tamanho:[/] {reduction:.1f}%"
            )
            return True

    except Exception as e:
        console.print(f"[bold red]❌ Erro ao processar o vídeo:[/] {str(e)}")
        return False
    finally:
        # Restaurar o diretório original
        os.chdir(original_dir)

def process_all_folders(base_folder, output_base):
    """
    Processa todas as pastas dentro da pasta base.

    Args:
        base_folder: Pasta contendo as subpastas com vídeos
        output_base: Pasta base onde serão criadas as subpastas com os vídeos processados
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