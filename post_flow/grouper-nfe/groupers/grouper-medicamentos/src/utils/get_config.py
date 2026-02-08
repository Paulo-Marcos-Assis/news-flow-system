from src.constants import PARAMS_PATH, CONFIG_PATH, PROJECT_ROOT
from pathlib import Path
import yaml
import os
from typing import Union # <-- ADICIONADO AQUI

def get_config(config: str, *keys: str):
    config_path = CONFIG_PATH    

    if not Path(config_path).exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")

    with open(config_path, "r") as f:
        params = yaml.safe_load(f)

    all_paths = params[config]

    # Resolve paths relative to the project root
    for key, path in all_paths.items():
        all_paths[key] = os.path.abspath(os.path.join(PROJECT_ROOT, path))

    if not keys:
        result = tuple(all_paths.values())
    else:
        invalid_keys = set(keys) - set(all_paths.keys())
        if invalid_keys:
            raise ValueError(
                f"Invalid key(s): {list(invalid_keys)}. "
                f"Valid keys are: {list(all_paths.keys())}"
            )
        result = tuple(all_paths[key] for key in keys)

    return result[0] if len(result) == 1 else result

# A LINHA ABAIXO FOI CORRIGIDA
def get_data_paths(*keys: str) -> Union[str, tuple[str, ...]]:
    """Retrieves data paths from the YAML configuration file.

    Args:
        *keys (str):
            Variable number of string key names for the paths to retrieve.
            If no keys are provided, all paths under the 'data' section
            in the config file will be returned.

         - "raw": Path to the raw data, typically in its
              original, unprocessed CSV format.
            - "cleaned": Path to the cleaned data, after being
              processed by a cleaning script (.py file).
            - "input_json": Path to the preprocessed data, transformed
              into a structured JSON format by a preprocessing script.
            - "filtered_json": Path to the final JSON data after
              domain-specific heuristics have been applied for filtering.
            - "filtered_json_structured": Path to the JSON data after
              being processed by structuring and deduplication heuristics.

    Returns:
        Union[str, tuple[str, ...]]:
            - If a single key is requested, returns the path string.
            - If multiple keys are requested, returns a tuple of paths.
            - If no keys are provided, returns a tuple with all paths.
    """
    return get_config("data_paths", *keys)

# A LINHA ABAIXO FOI CORRIGIDA
def get_prompt_template (*keys: str) -> Union[str, tuple[str, ...]]:
        return get_config("prompt", *keys)

def get_ollama_host() -> str:
    with open(CONFIG_PATH, "r") as f:
        config = yaml.safe_load(f)
    return config["ollama"]["host"]

# A LINHA ABAIXO FOI CORRIGIDA
def get_results_path (*keys: str) -> Union[str, tuple[str, ...]]:
         return get_config("result_paths", *keys)

def get_raw_config(section: str, key: str):
    """Retrieves a raw configuration value from config.yaml without path processing."""
    config_path = CONFIG_PATH
    if not Path(config_path).exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")

    with open(config_path, "r") as f:
        config = yaml.safe_load(f)

    try:
        return config[section][key]
    except KeyError:
        raise KeyError(f"Key '{key}' not found in section '{section}' of config.yaml")



def get_param(key: str):
    """
    Retrieves a parameter value from the params.yaml file.

    Args:
        key (str): The key for the parameter to retrieve.

    Returns:
        The parameter value.

    Raises:
        FileNotFoundError: If the params file does not exist.
        KeyError: If the key is not found in the params file.
    """
    params_path = PARAMS_PATH

    if not Path(params_path).exists():
        raise FileNotFoundError(f"Params file not found: {params_path}")

    with open(params_path, 'r') as f:
        params = yaml.safe_load(f)

    if key in params:
        value = params[key]
        if "path" in key:
            return os.path.abspath(os.path.join(PROJECT_ROOT, value))
        return value
    else:
        raise KeyError(f"Key '{key}' not found in params.yaml")