import os
import sys
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(parent_dir)
project_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(project_dir)
import Panda as pd
import yaml
import pytest
import importlib.util

def load_module():
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '.'))
    module_path = os.path.join(base_dir, 'CheckPeSysconfig_20.py')
    spec = importlib.util.spec_from_file_location('CheckPeSysconfig_20_module', module_path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod
yaml_path = os.path.join(os.path.dirname(__file__), 'CheckPeSysconfig_20.yaml')
pkl_path = '/tmp/test_data_status_checkpesysconfig.pkl'
file_path = '/tmp/test_pesysconfig_path'
backup_path = '/tmp/test_checkpesysconfig_bak'

@pytest.fixture(autouse=True)
def prepare_files():
    if os.path.exists(yaml_path):
        os.system(f'cp {yaml_path} /tmp/CheckPeSysconfig_20.yaml')

def build_instance():
    pass

def test_init():
    pass

def test_finalfix():
    pass

def test_fix_sets_mode_and_status(monkeypatch):
    pass

def test_check_permission_is_expected(monkeypatch):
    pass

def test_check_permission_not_expected(monkeypatch):
    pass

def test_rollback_updates_status_when_check_fails(monkeypatch):
    pass

def test_reset(monkeypatch):
    pass

def test_get_des():
    pass