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

# 1. Inicialização e Configuração
console = Console()
# 2. Funções de Utilidade para Tempo
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

# 3. Funções de Análise de Vídeo
def get_video_resolution(video_path):
    """
    Obtém a resolução do vídeo usando FFmpeg.

    Args:
        video_path: Caminho do arquivo de vídeo

    Returns:
        tuple: (width, height) se sucesso
        None: se não encontrar resolução

    Raises:
        FileNotFoundError: Se o FFmpeg não for encontrado
        RuntimeError: Se houver erro ao processar o vídeo
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

        except FileNotFoundError:
            console.print("[bold red]Erro:[/] FFmpeg não encontrado no sistema")
            raise  # Propaga o FileNotFoundError

        except Exception as e:
            console.print(f"[bold red]Erro ao obter resolução do vídeo:[/] {str(e)}")
            raise RuntimeError(f"Erro ao processar vídeo: {str(e)}")

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

# 4. Funções de Busca de Arquivos
def find_video_and_subtitle(folder):
    """
    Encontra o arquivo de vídeo e legenda em uma pasta.
    Agora retorna o vídeo mesmo se não encontrar legenda.
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

    if not video_file:
        console.print("[bold red]⚠️ Aviso:[/] Vídeo não encontrado!")
    elif not subtitle_file:
        console.print("[bold yellow]ℹ️ Info:[/] Nenhuma legenda encontrada. Será adicionada apenas a logo.")

    return video_file, subtitle_file

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

def burn_subtitle_and_logo(input_folder, output_folder, assets_dir=None):
    """
    Queima a legenda (se existir) e a logo no vídeo usando FFmpeg.
    """
    # Localizar arquivos
    video_file, subtitle_file = find_video_and_subtitle(input_folder)
    if not video_file:
        console.print(
            f"[bold red]❌ Erro:[/] Vídeo não encontrado em {input_folder}"
        )
        return False

    # Configurar output
    output_folder = Path(output_folder)
    output_folder.mkdir(parents=True, exist_ok=True)
    output_suffix = "_legendado" if subtitle_file else "_logo"
    output_name = f"{video_file.stem}{output_suffix}{video_file.suffix}"
    output_path = output_folder / output_name

    # Verificar resolução para logo apropriada
    resolution = get_video_resolution(video_file)
    if not resolution:
        console.print(
            "[bold red]❌ Erro:[/] Não foi possível determinar a resolução do vídeo."
        )
        return False

    width, height = resolution
    try:
        logo_file = get_appropriate_logo(height, assets_dir=assets_dir)
        if not logo_file.exists():
            console.print(
                f"[bold red]❌ Erro:[/] Arquivo de logo não encontrado: {logo_file}"
            )
            return False
    except Exception as e:
        console.print(f"[bold red]❌ Erro ao obter logo:[/] {str(e)}")
        return False

    total_duration = get_video_duration(video_file)
    if not total_duration:
        console.print(
            "[bold yellow]⚠️ Aviso:[/] Não foi possível determinar a duração do vídeo."
        )
        total_duration = 100

    # Salvar diretório atual
    original_dir = os.getcwd()

    try:
        # Mudar para o diretório do vídeo
        os.chdir(video_file.parent)

        # Usar nomes de arquivo relativos
        video_name = video_file.name
        subtitle_name = subtitle_file.name if subtitle_file else None
        logo_path = str(logo_file.absolute())  # Precisa ser caminho absoluto pois está em outro diretório
        output_path_abs = str(output_path.absolute())

        # Montar comando FFmpeg baseado na presença ou não de legenda
        if subtitle_file:
            # Primeiro, adiciona a legenda
            subtitle_command = [
                "ffmpeg",
                "-i",
                video_name,
                "-vf",
                f"subtitles={subtitle_name}",
                "-c:v",
                "libx264",
                "-preset",
                "faster",
                "-crf",
                "18",
                "-c:a",
                "copy",
                "temp_with_subs.mp4"
            ]

            # Depois, adiciona a logo
            logo_command = [
                "ffmpeg",
                "-i",
                "temp_with_subs.mp4",
                "-i",
                logo_path,
                "-filter_complex",
                "[0:v][1:v]overlay=W-w:0",
                "-c:v",
                "libx264",
                "-preset",
                "faster",
                "-crf",
                "18",
                "-c:a",
                "copy",
                "-y",
                output_path_abs
            ]
        else:
            # Comando apenas com logo
            logo_command = [
                "ffmpeg",
                "-i",
                video_name,
                "-i",
                logo_path,
                "-filter_complex",
                "[0:v][1:v]overlay=W-w:0",
                "-c:v",
                "libx264",
                "-preset",
                "faster",
                "-crf",
                "18",
                "-c:a",
                "copy",
                "-y",
                output_path_abs
            ]

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
                    f"[cyan]Processando {video_file.name}" +
                    (" (legenda + logo)" if subtitle_file else " (apenas logo)"),
                    total=100
                )

                if subtitle_file:
                    # Primeiro processo: adicionar legendas
                    process = subprocess.Popen(
                        subtitle_command,
                        stderr=subprocess.PIPE,
                        stdout=subprocess.PIPE,
                        universal_newlines=True
                    )

                    # Monitorar progresso
                    while process.poll() is None:
                        line = process.stderr.readline()
                        if line:
                            if "Error" in line or "Invalid" in line:
                                console.print(f"[yellow]⚠️ FFmpeg:[/] {line.strip()}")

                            time_match = re.search(r"time=(\d{2}:\d{2}):(\d{2}\.\d{2})", line)
                            if time_match:
                                current_time = parse_time(time_match.group(0))
                                percent = min(int((current_time / total_duration) * 50), 50)  # Primeira metade do progresso
                                progress.update(task, completed=percent)

                    if process.returncode != 0:
                        raise RuntimeError("Falha ao adicionar legendas")

                # Processo final: adicionar logo
                process = subprocess.Popen(
                    logo_command,
                    stderr=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    universal_newlines=True
                )

                # Monitorar progresso
                start_percent = 50 if subtitle_file else 0
                while process.poll() is None:
                    line = process.stderr.readline()
                    if line:
                        if "Error" in line or "Invalid" in line:
                            console.print(f"[yellow]⚠️ FFmpeg:[/] {line.strip()}")

                        time_match = re.search(r"time=(\d{2}:\d{2}):(\d{2}\.\d{2})", line)
                        if time_match:
                            current_time = parse_time(time_match.group(0))
                            percent = min(int((current_time / total_duration) * 50), 50)  # Segunda metade do progresso
                            progress.update(task, completed=start_percent + percent)

                if process.returncode == 0:
                    success_msg = "Legenda e logo adicionadas" if subtitle_file else "Logo adicionada"
                    console.print(
                        f"[bold green]✓ {success_msg} com sucesso:[/] {output_path}"
                    )
                    return True
                else:
                    raise RuntimeError("Falha ao adicionar logo")

        except Exception as e:
            console.print(f"[bold red]❌ Erro ao processar o vídeo:[/] {str(e)}")
            return False

        finally:
            # Limpar arquivo temporário se existir
            if subtitle_file and os.path.exists("temp_with_subs.mp4"):
                os.remove("temp_with_subs.mp4")

    finally:
        # Restaurar diretório original
        os.chdir(original_dir)
        
# 6. Função de Processamento em Lote
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

# 7. Ponto de Entrada do Script
if __name__ == "__main__":
    # 7.1 Configuração inicial
    console = Console()

    # 7.2 Interface do usuário
    console.print(
        Panel.fit(
            "[bold cyan]🎬 Processador de Legendas[/]\n"
            "[italic]Adiciona legendas e logo permanentemente aos seus vídeos[/]",
            border_style="cyan",
        )
    )

    # 7.3 Configuração dos diretórios
    script_dir = Path(__file__).parent
    base_folder = script_dir / "input"
    output_base = script_dir / "output"

    # 7.4 Início do processamento
    process_all_folders(base_folder, output_base)