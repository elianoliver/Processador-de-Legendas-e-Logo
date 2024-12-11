from pathlib import Path
from rich.panel import Panel
from modules.config import console
from modules.processor import process_all_folders

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