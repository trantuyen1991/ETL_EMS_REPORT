"""
Config Loader Module

Responsible for:
- Loading environment variables (.env)
- Loading YAML configuration (app.yaml)
- Merging all configurations into a unified structure

This module should be the single source of truth for configuration across the project.
"""

import os
import re
from typing import Dict, Any

import yaml

from src.utils.logger import get_logger

logger = get_logger(__name__)


def load_env(env_path: str) -> Dict[str, Any]:
    """
    Load environment variables from .env file.

    Args:
        env_path (str): Path to .env file

    Returns:
        Dict[str, Any]: Environment configuration dictionary

    Raises:
        FileNotFoundError: If .env file does not exist
        ValueError: If invalid line format is found
        RuntimeError: If loading fails
    """
    config: Dict[str, Any] = {}

    logger.info("Loading .env file. path=%s", env_path)

    if not os.path.exists(env_path):
        logger.error(".env file not found. path=%s", env_path)
        raise FileNotFoundError(f".env file not found at: {env_path}")

    try:
        with open(env_path, "r", encoding="utf-8") as f:
            for line_number, line in enumerate(f, start=1):
                line = line.strip()

                if not line or line.startswith("#"):
                    continue

                if "=" not in line:
                    logger.error(
                        "Invalid .env format detected. path=%s line_number=%s line=%s",
                        env_path,
                        line_number,
                        line,
                    )
                    raise ValueError(
                        f"Invalid format in .env at line {line_number}: {line}"
                    )

                key, value = line.split("=", 1)
                key = key.strip()
                value = value.strip()

                config[key] = value

        logger.info(
            ".env file loaded successfully. path=%s key_count=%s",
            env_path,
            len(config),
        )

    except Exception as e:
        logger.exception("Failed to load .env file. path=%s", env_path)
        raise RuntimeError(f"Error loading .env file: {e}") from e

    return config


def load_yaml(yaml_path: str) -> Dict[str, Any]:
    """
    Load configuration from YAML file.

    Args:
        yaml_path (str): Path to YAML config file

    Returns:
        Dict[str, Any]: YAML configuration dictionary

    Raises:
        FileNotFoundError: If YAML file does not exist
        RuntimeError: If YAML loading fails
    """
    logger.info("Loading YAML config file. path=%s", yaml_path)

    if not os.path.exists(yaml_path):
        logger.error("YAML config file not found. path=%s", yaml_path)
        raise FileNotFoundError(f"YAML config file not found at: {yaml_path}")

    try:
        with open(yaml_path, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)

        if config is None:
            logger.warning("YAML file is empty. path=%s", yaml_path)
            return {}

        if not isinstance(config, dict):
            logger.error(
                "Invalid YAML root type. path=%s actual_type=%s",
                yaml_path,
                type(config).__name__,
            )
            raise ValueError("YAML root content must be a dictionary")

        logger.info(
            "YAML config loaded successfully. path=%s top_level_keys=%s",
            yaml_path,
            list(config.keys()),
        )

        return config

    except Exception as e:
        logger.exception("Failed to load YAML config file. path=%s", yaml_path)
        raise RuntimeError(f"Error loading YAML config file: {e}") from e


def resolve_env_variables(data: Any, env: Dict[str, str]) -> Any:
    """
    Recursively replace ${VAR} in YAML config using env values.

    Args:
        data (Any): YAML data (dict, list, or value)
        env (Dict[str, str]): environment variables

    Returns:
        Any: resolved data
    """
    pattern = re.compile(r"\$\{(.+?)\}")

    if isinstance(data, dict):
        return {k: resolve_env_variables(v, env) for k, v in data.items()}

    if isinstance(data, list):
        return [resolve_env_variables(item, env) for item in data]

    if isinstance(data, str):
        matches = pattern.findall(data)
        for match in matches:
            if match in env:
                logger.debug("Resolved env variable in YAML. variable=%s", match)
                data = data.replace(f"${{{match}}}", env[match])
            else:
                logger.warning(
                    "YAML references undefined env variable. variable=%s",
                    match,
                )
        return data

    return data


def merge_config(env: Dict[str, str], yaml_cfg: Dict[str, Any]) -> Dict[str, Any]:
    """
    Merge environment variables and YAML config.

    Args:
        env (Dict[str, str]): environment variables
        yaml_cfg (Dict[str, Any]): YAML config

    Returns:
        Dict[str, Any]: merged and resolved config
    """
    logger.info(
        "Merging configuration sources. env_key_count=%s yaml_top_level_keys=%s",
        len(env),
        list(yaml_cfg.keys()),
    )

    # Step 1: resolve ${VAR} inside YAML
    resolved_yaml = resolve_env_variables(yaml_cfg, env)

    # Step 2: attach env for reference/debug if needed
    merged = {
        "env": env,
        "config": resolved_yaml
    }

    logger.info(
        "Configuration merged successfully. sections=%s",
        list(merged.keys()),
    )

    return merged


def load_config(env_path: str, yaml_path: str) -> Dict[str, Any]:
    """
    Load full application configuration.

    Args:
        env_path (str): path to .env file
        yaml_path (str): path to YAML config

    Returns:
        Dict[str, Any]: merged config
    """
    logger.info(
        "Starting application config load. env_path=%s yaml_path=%s",
        env_path,
        yaml_path,
    )

    env = load_env(env_path)
    yaml_cfg = load_yaml(yaml_path)
    merged_config = merge_config(env, yaml_cfg)

    logger.info("Application config loaded successfully.")

    return merged_config