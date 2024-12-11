from pathlib import Path
from rich.table import Table
from .config import console, VIDEO_EXTENSIONS, SUBTITLE_EXTENSIONS

def find_video_and_subtitle(folder):
    """
    Encontra o arquivo de vídeo e legenda em uma pasta.
    """
    video_file = None
    subtitle_file = None
    folder_path = Path(folder)

    table = Table(title=f"\nArquivos em [cyan]{folder_path}[/]")
    table.add_column("Tipo", style="bold magenta")
    table.add_column("Arquivo", style="green")

    for file in folder_path.iterdir():
        file_lower = str(file).lower()
        if file_lower.endswith(VIDEO_EXTENSIONS) and not video_file:
            video_file = file
            table.add_row("Vídeo", str(file))
        elif file_lower.endswith(SUBTITLE_EXTENSIONS) and not subtitle_file:
            subtitle_file = file
            table.add_row("Legenda", str(file))

        if video_file and subtitle_file:
            break

    console.print(table)

    if not video_file:
        console.print("[bold red]⚠️ Aviso:[/] Vídeo não encontrado!")
    elif not subtitle_file:
        console.print("[bold yellow]ℹ️ Info:[/] Nenhuma legenda encontrada. Será adicionada apenas a logo.")

    return video_file, subtitle_file

def should_process_video(video_path, output_folder):
    """
    Verifica se o vídeo deve ser processado.
    """
    if not video_path:
        return False, "Vídeo não encontrado"

    possible_suffixes = ["_legendado.mp4", "_logo.mp4"]
    for suffix in possible_suffixes:
        output_path = output_folder / f"{video_path.stem}{suffix}"
        if output_path.exists():
            return False, f"Arquivo já processado: {output_path}"

    return True, None