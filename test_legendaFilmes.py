import pytest
from pathlib import Path
import tempfile
import shutil
from datetime import datetime
import os
import sys

# Adiciona o diretório do projeto ao PYTHONPATH
sys.path.append(str(Path(__file__).parent.parent))

# Importa as funções do seu módulo principal
from legendaFilmes import (
    parse_time,
    format_time,
    get_video_resolution,
    get_video_duration,
    find_video_and_subtitle,
    get_appropriate_logo,
    burn_subtitle_and_logo
)

# 1. Configuração dos testes
@pytest.fixture
def temp_test_dir():
    """Cria um diretório temporário para testes"""
    temp_dir = tempfile.mkdtemp()
    yield Path(temp_dir)
    shutil.rmtree(temp_dir)

@pytest.fixture
def sample_video_dir(temp_test_dir):
    """Cria uma estrutura de diretório de teste com arquivos simulados"""
    video_dir = temp_test_dir / "test_video"
    video_dir.mkdir()

    # Cria arquivos dummy
    (video_dir / "video.mp4").touch()
    (video_dir / "subtitle.srt").touch()

    return video_dir

@pytest.fixture
def assets_dir(temp_test_dir):
    """Cria diretório de assets com logos"""
    assets_dir = temp_test_dir / "assets"
    assets_dir.mkdir()

    # Cria logos dummy
    (assets_dir / "720 overlay.png").touch()
    (assets_dir / "1080 overlay.png").touch()

    return assets_dir

# 2. Testes de Funções de Tempo
def test_parse_time():
    """Testa a função parse_time"""
    assert parse_time("00:00:00.00") == 0
    assert parse_time("00:01:00.00") == 60
    assert parse_time("01:00:00.00") == 3600
    assert parse_time("01:30:45.00") == 5445
    assert parse_time("invalid") == 0

def test_format_time():
    """Testa a função format_time"""
    assert format_time(0) == "00:00:00"
    assert format_time(60) == "00:01:00"
    assert format_time(3600) == "01:00:00"
    assert format_time(5445) == "01:30:45"

# 3. Testes de Análise de Vídeo
def test_get_video_resolution(mocker):
    """Testa a função get_video_resolution com mock do FFmpeg"""
    # Simula a saída do FFmpeg
    mock_result = mocker.Mock()
    mock_result.stderr = "Stream #0:0: Video: h264, yuv420p, 1920x1080"
    mocker.patch('subprocess.run', return_value=mock_result)

    result = get_video_resolution("dummy.mp4")
    assert result == (1920, 1080)

def test_get_video_duration(mocker):
    """Testa a função get_video_duration com mock do FFmpeg"""
    # Simula a saída do FFmpeg
    mock_result = mocker.Mock()
    mock_result.stderr = "Duration: 00:30:00.00"
    mocker.patch('subprocess.run', return_value=mock_result)

    duration = get_video_duration("dummy.mp4")
    assert duration == 1800  # 30 minutos em segundos

# 4. Testes de Busca de Arquivos
def test_find_video_and_subtitle(sample_video_dir):
    """Testa a função find_video_and_subtitle"""
    video_file, subtitle_file = find_video_and_subtitle(sample_video_dir)

    assert video_file.name == "video.mp4"
    assert subtitle_file.name == "subtitle.srt"

def test_get_appropriate_logo(assets_dir):
    """Testa a função get_appropriate_logo"""
    # Cria os arquivos de logo no diretório de teste
    logo_720 = assets_dir / "720 overlay.png"
    logo_1080 = assets_dir / "1080 overlay.png"
    logo_720.touch()
    logo_1080.touch()

    # Testa para diferentes resoluções
    result_720 = get_appropriate_logo(720, assets_dir=assets_dir)
    result_1080 = get_appropriate_logo(1080, assets_dir=assets_dir)
    result_900 = get_appropriate_logo(900, assets_dir=assets_dir)  # Deve escolher o mais próximo

    # Verifica os resultados
    assert result_720.name == "720 overlay.png"
    assert result_1080.name == "1080 overlay.png"
    assert result_900.name == "720 overlay.png"  # Mais próximo de 720

    # Verifica se os caminhos são corretos
    assert result_720 == logo_720
    assert result_1080 == logo_1080
    assert result_900 == logo_720

def test_burn_subtitle_and_logo_integration(sample_video_dir, temp_test_dir, mocker):
    """Teste de integração do processo de queima de legenda e logo"""
    # Configura o diretório de saída
    output_dir = temp_test_dir / "output"

    # Configura os arquivos de teste
    video_path = sample_video_dir / "video.mp4"
    subtitle_path = sample_video_dir / "subtitle.srt"
    logo_path = temp_test_dir / "assets" / "1080 overlay.png"

    # Garante que os arquivos existam
    video_path.parent.mkdir(exist_ok=True)
    video_path.touch()
    subtitle_path.touch()
    logo_path.parent.mkdir(exist_ok=True)
    logo_path.touch()

    # Mock das funções que dependem do FFmpeg
    mocker.patch(
        'legendaFilmes.get_video_resolution',
        return_value=(1920, 1080)
    )
    mocker.patch(
        'legendaFilmes.get_video_duration',
        return_value=1800
    )
    mocker.patch(
        'legendaFilmes.get_appropriate_logo',
        return_value=logo_path
    )

    # Mock do processo FFmpeg
    mock_process = mocker.Mock()
    mock_process.poll.side_effect = [None, 0]  # Retorna None na primeira chamada e 0 na segunda
    mock_process.returncode = 0
    mock_process.stderr = mocker.Mock()
    mock_process.stderr.readline.return_value = "time=00:00:01.00"
    mocker.patch('subprocess.Popen', return_value=mock_process)

    # Executa a função
    result = burn_subtitle_and_logo(sample_video_dir, output_dir)

    # Verificações
    assert result == True
    assert (output_dir / f"{video_path.stem}_legendado{video_path.suffix}").parent.exists()

# 6. Testes de Erro
def test_error_handling(mocker):
    """Testa o tratamento de erros nas funções principais"""

    # 1. Testa FileNotFoundError (FFmpeg não encontrado)
    mocker.patch('subprocess.run', side_effect=FileNotFoundError)
    with pytest.raises(FileNotFoundError):
        get_video_resolution("video.mp4")

    # 2. Testa erro genérico do FFmpeg
    mocker.patch('subprocess.run', side_effect=Exception("Erro FFmpeg"))
    with pytest.raises(RuntimeError) as exc_info:
        get_video_resolution("video.mp4")
    assert "Erro ao processar vídeo" in str(exc_info.value)

    # 3. Testa vídeo sem resolução detectável
    mock_result = mocker.Mock()
    mock_result.stderr = "Stream #0:0: Video: h264"  # Sem resolução
    mocker.patch('subprocess.run', return_value=mock_result)
    assert get_video_resolution("video.mp4") is None

    # 4. Testa diretório vazio
    with tempfile.TemporaryDirectory() as temp_dir:
        video_file, subtitle_file = find_video_and_subtitle(temp_dir)
        assert video_file is None
        assert subtitle_file is None

    # 5. Testa logo não encontrada
    with tempfile.TemporaryDirectory() as temp_dir:
        assets_dir = Path(temp_dir) / "assets"
        assets_dir.mkdir()  # Cria o diretório assets vazio
        # Como o diretório está vazio (sem logos), deve levantar FileNotFoundError
        with pytest.raises(FileNotFoundError) as exc_info:
            get_appropriate_logo(720, assets_dir=assets_dir)
        assert "Arquivo de logo não encontrado" in str(exc_info.value)

if __name__ == "__main__":
    pytest.main(["-v", __file__])