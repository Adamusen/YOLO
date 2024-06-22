import sys
from pathlib import Path

import pytest
import torch
from hydra import compose, initialize

project_root = Path(__file__).resolve().parent.parent
sys.path.append(str(project_root))

from yolo import Config, Vec2Box, create_model
from yolo.model.yolo import YOLO
from yolo.tools.data_loader import StreamDataLoader, YoloDataLoader
from yolo.utils.logging_utils import ProgressLogger, set_seed


def pytest_configure(config):
    config.addinivalue_line("markers", "requires_cuda: mark test to run only if CUDA is available")


def get_cfg(overrides=[]) -> Config:
    config_path = "../yolo/config"
    with initialize(config_path=config_path, version_base=None):
        cfg: Config = compose(config_name="config", overrides=overrides)
        set_seed(cfg.lucky_number)
        return cfg


@pytest.fixture(scope="session")
def train_cfg() -> Config:
    return get_cfg(overrides=["task=train", "dataset=mock"])


@pytest.fixture(scope="session")
def validation_cfg():
    return get_cfg(overrides=["task=validation", "dataset=mock"])


@pytest.fixture(scope="session")
def inference_cfg():
    return get_cfg(overrides=["task=inference"])


@pytest.fixture(scope="session")
def device():
    return torch.device("cuda" if torch.cuda.is_available() else "cpu")


@pytest.fixture(scope="session")
def train_progress_logger(train_cfg: Config):
    progress_logger = ProgressLogger(train_cfg, exp_name=train_cfg.name)
    return progress_logger


@pytest.fixture(scope="session")
def validation_progress_logger(validation_cfg: Config):
    progress_logger = ProgressLogger(validation_cfg, exp_name=validation_cfg.name)
    return progress_logger


@pytest.fixture(scope="session")
def model(train_cfg: Config, device) -> YOLO:
    model = create_model(train_cfg.model)
    return model.to(device)


@pytest.fixture(scope="session")
def vec2box(train_cfg: Config, model: YOLO, device) -> Vec2Box:
    vec2box = Vec2Box(model, train_cfg.image_size, device)
    return vec2box


@pytest.fixture(scope="session")
def train_dataloader(train_cfg: Config):
    return YoloDataLoader(train_cfg.task.data, train_cfg.dataset, train_cfg.task.task)


@pytest.fixture(scope="session")
def validation_dataloader(validation_cfg: Config):
    return YoloDataLoader(validation_cfg.task.data, validation_cfg.dataset, validation_cfg.task.task)


@pytest.fixture(scope="session")
def file_stream_data_loader(inference_cfg: Config):
    return StreamDataLoader(inference_cfg.task.data)


@pytest.fixture(scope="session")
def directory_stream_data_loader(inference_cfg: Config):
    inference_cfg.task.data.source = "tests/data/images/train"
    return StreamDataLoader(inference_cfg.task.data)
