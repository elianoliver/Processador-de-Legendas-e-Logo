def create_ffmpeg_command(video_file, subtitle_file, logo_file, output_path, video_options, audio_options):
    """
    Cria o comando FFmpeg unificado para processamento.
    """
    subtitle_filename = subtitle_file.name if subtitle_file else None

    if subtitle_file:
        return [
            "ffmpeg", # Comando base do FFmpeg
            "-i", str(video_file), # Primeiro input: arquivo de vídeo
            "-i", str(logo_file), # Segundo input: arquivo da logo
            "-f", "mp4",  # Força o formato de saída para MP4
            "-filter_complex", # Início da cadeia de filtros complexos
            f"subtitles='{subtitle_filename}',overlay=W-w:0", # Filtros
        ] + video_options + audio_options + [ # Filtros
            "-y", # Sobrescrever arquivo se existir
            str(output_path) # Caminho do arquivo de saída
        ]
    else:
        return [
            "ffmpeg",
            "-i", str(video_file),
            "-i", str(logo_file),
            "-filter_complex", "overlay=W-w:0", # Apenas o filtro da logo
        ] + video_options + audio_options + [ # Apenas o filtro da logo
            "-y", str(output_path)
        ]