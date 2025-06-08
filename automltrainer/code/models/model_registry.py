import importlib
import inspect
from pathlib import Path
from typing import Dict, List
from .base_model import BaseModelConfig

class ModelRegistry:
    """Automatically discover and register all model configurations"""
    
    def __init__(self):
        self._models = {}
        self._discover_models()
    
    def _discover_models(self):
        """Automatically discover all model configurations"""
        models_dir = Path(__file__).parent
        
        # Look for Python files (not subdirectories)
        for py_file in models_dir.glob("*.py"):
            if py_file.name.startswith("_") or py_file.name in ["base_model.py", "model_registry.py"]:
                continue
                
            module_name = py_file.stem
            try:
                # Import the module
                module = importlib.import_module(f"models.{module_name}")
                
                # Find the config class
                for name, obj in inspect.getmembers(module, inspect.isclass):
                    if (issubclass(obj, BaseModelConfig) and 
                        obj != BaseModelConfig and 
                        name.endswith('Config')):
                        
                        config_instance = obj()
                        model_name = config_instance.get_model_name()
                        self._models[model_name] = config_instance
                        print(f"Registered model: {model_name}")
                        break
                        
            except Exception as e:
                print(f"Failed to load model from {py_file}: {e}")
    
    def get_model_config(self, model_name: str) -> BaseModelConfig:
        """Get model configuration by name"""
        if model_name not in self._models:
            raise ValueError(f"Model '{model_name}' not found. Available: {self.list_models()}")
        return self._models[model_name]
    
    def list_models(self) -> List[str]:
        """List all available models"""
        return list(self._models.keys())
    
    def get_all_default_configs(self) -> Dict[str, Dict]:
        """Get default configurations for all models"""
        all_configs = {}
        for model_name, config in self._models.items():
            all_configs.update(config.get_default_configs())
        return all_configs