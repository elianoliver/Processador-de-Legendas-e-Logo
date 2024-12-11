from .config import console

def convert_subtitle_to_utf8(subtitle_path):
    """
    Verifica a codificação da legenda e converte para UTF-8 se necessário.
    """
    encodings = ['utf-8', 'iso-8859-1', 'windows-1252', 'ansi']
    utf8_path = subtitle_path.parent / f"{subtitle_path.stem}_utf8{subtitle_path.suffix}"

    if utf8_path.exists():
        return utf8_path

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

    try:
        with open(utf8_path, 'w', encoding='utf-8') as f:
            f.write(content)
        console.print(f"[bold green]✓ Legenda convertida para UTF-8:[/] {utf8_path}")
        return utf8_path
    except Exception as e:
        console.print(f"[bold red]❌ Erro ao converter legenda para UTF-8:[/] {str(e)}")
        return None