# modules/video_analysis.py
import subprocess
import re
from pathlib import Path
from .config import console

def get_video_metadata(video_path):
    """
    Obtém todos os metadados relevantes do vídeo em uma única chamada FFmpeg.
    Usa codificação utf-8 com tratamento de erros para lidar com caracteres especiais.
    """
    with console.status("[bold yellow]Analisando metadados do vídeo...", spinner="dots"):
        cmd = ["ffmpeg", "-i", str(video_path)]
        try:
            # Configurar o processo para usar utf-8 e ignorar erros de codificação
            process = subprocess.Popen(
                cmd,
                stderr=subprocess.PIPE,
                stdout=subprocess.PIPE,
                universal_newlines=False  # Mudamos para False para obter bytes brutos
            )

            # Capturar a saída e decodificar com tratamento de erros
            _, stderr_bytes = process.communicate()
            stderr = stderr_bytes.decode('utf-8', errors='replace')

            # Extrair resolução
            resolution_match = re.search(r"Stream.*Video:.* (\d+)x(\d+)", stderr)
            width = height = None
            if resolution_match:
                width = int(resolution_match.group(1))
                height = int(resolution_match.group(2))

            # Extrair duração
            duration_match = re.search(
                r"Duration: (\d{2}):(\d{2}):(\d{2})\.(\d{2})", stderr
            )
            duration = None
            if duration_match:
                hours = int(duration_match.group(1))
                minutes = int(duration_match.group(2))
                seconds = int(duration_match.group(3))
                duration = hours * 3600 + minutes * 60 + seconds

            if not resolution_match and not duration_match:
                console.print("[bold yellow]⚠️ Aviso:[/] Não foi possível extrair todos os metadados do vídeo")
                console.print(f"[bold blue]ℹ️ Saída do FFmpeg:[/] {stderr}")

            return {
                "resolution": (width, height) if width and height else None,
                "duration": duration
            }

        except FileNotFoundError:
            console.print("[bold red]Erro:[/] FFmpeg não encontrado no sistema")
            raise
        except Exception as e:
            console.print(f"[bold red]Erro ao obter metadados do vídeo:[/] {str(e)}")
            console.print("[bold yellow]Detalhes adicionais:[/] Verifique se o arquivo de vídeo está corrompido ou se tem caracteres especiais no nome")
            raise RuntimeError(f"Erro ao processar vídeo: {str(e)}")

def get_appropriate_logo(height, assets_dir=None):
    """
    Determina qual versão da logo usar baseado na altura do vídeo.
    """
    if assets_dir is None:
        assets_dir = Path(__file__).parent.parent / "assets"

    if not assets_dir.exists():
        raise FileNotFoundError(f"Diretório de assets não encontrado: {assets_dir}")

    logos = {
        720: assets_dir / "720 overlay.png",
        1080: assets_dir / "1080 overlay.png"
    }

    for resolution, logo_path in logos.items():
        if not logo_path.exists():
            raise FileNotFoundError(f"Arquivo de logo não encontrado: {logo_path}")

    closest_resolution = min(logos.keys(), key=lambda x: abs(x - height))
    return logos[closest_resolution]