import re

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