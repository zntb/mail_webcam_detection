import yaml
import os
import sys
from pathlib import Path
import logging
import shutil
import numpy as np
import time

class Config:
    """Enhanced configuration management with robust path handling."""
    
    def __init__(self, config_path="config.yaml"):
        """Initialize configuration with thorough validation."""
        self.config_path = Path(config_path).absolute()
        self.logger = logging.getLogger(__name__)
        self._default_config = self._get_default_config()
        self.load_config()
        self._validate_paths()
        self.frame_count = 0
        self.warmup_frames = 30  # Number of frames to ignore on startup
        self.start_time = time.time()
        self.min_startup_delay = 3  # seconds
        
    def _get_default_config(self):
        """Return validated default configuration."""
        return {
            # Camera settings
            'camera_index': 0,
            'frame_width': 640,
            'frame_height': 480,
            'fps': 30,
            
            # Motion detection
            'sensitivity': 40,
            'motion_threshold': 25,
            'min_contour_area': 800,
            'motion_cooldown': 45,
            
            # File handling (enhanced)
            'images_dir': str(Path.cwd() / 'images'),  # Absolute path by default
            'max_images': 50,
            'image_format': 'jpg',  # Added format specification
            'image_quality': 90,    # Quality for JPEG
            
            # Display
            'show_video': True,
            'show_debug': False,
            
            # Email
            'email_enabled': True,
            
            # System
            'max_retries': 3,       # Added for file operations
            'retry_delay': 0.1,     # Seconds between retries
            
            # Logging
            'log_level': 'INFO',
            'log_file': 'motion_detector.log'
        }
        
    def load_config(self):
        """Load configuration with enhanced error recovery."""
        try:
            # Create default config file if missing
            if not self.config_path.exists():
                self.logger.warning(f"Config file not found at {self.config_path}")
                self._save_default_config()
                return
            
            with open(self.config_path, 'r') as f:
                user_config = yaml.safe_load(f) or {}
                
            # Deep merge with validation
            self._merge_configs(self._default_config, user_config)
            
            # Set attributes
            for key, value in self._default_config.items():
                setattr(self, key, value)
                
            self.logger.info(f"Loaded config from {self.config_path}")
            
        except Exception as e:
            self.logger.error(f"Config load error: {e}. Using defaults.")
            for key, value in self._default_config.items():
                setattr(self, key, value)
                
    def _merge_configs(self, default, user):
        """Safe recursive config merge with type checking."""
        for key, value in user.items():
            if key in default:
                if isinstance(default[key], dict) and isinstance(value, dict):
                    self._merge_configs(default[key], value)
                else:
                    # Type validation
                    if type(default[key]) == type(value) or default[key] is None:
                        default[key] = value
                    else:
                        self.logger.warning(
                            f"Type mismatch for {key}: "
                            f"expected {type(default[key])}, got {type(value)}. "
                            f"Keeping default value."
                        )
            else:
                self.logger.warning(f"Ignoring unknown config key: {key}")
                
    def _validate_paths(self):
        """Validate all path-related configurations."""
        try:
            # Convert to absolute path and create directory
            self.images_dir = Path(self.images_dir).absolute()
            self.images_dir.mkdir(parents=True, exist_ok=True)
            
            # Verify write permission
            test_file = self.images_dir / 'write_test.tmp'
            for _ in range(self.max_retries):
                try:
                    test_file.write_text('test')
                    test_file.unlink()
                    break
                except Exception as e:
                    self.logger.warning(f"Write test failed (attempt {_+1}): {e}")
                    time.sleep(self.retry_delay)
            else:
                raise RuntimeError(f"Cannot write to {self.images_dir}")
                
            # Verify image format
            if self.image_format.lower() not in ['jpg', 'jpeg', 'png']:
                raise ValueError(f"Unsupported image format: {self.image_format}")
                
            # Validate image quality
            if not (0 <= self.image_quality <= 100):
                raise ValueError(f"Invalid image quality: {self.image_quality}")
                
        except Exception as e:
            self.logger.error(f"Configuration validation failed: {e}")
            raise
            
    def _save_default_config(self):
        """Save default config with organized structure."""
        try:
            config_data = {
                'camera': {
                    'index': self._default_config['camera_index'],
                    'frame_width': self._default_config['frame_width'],
                    'frame_height': self._default_config['frame_height'],
                    'fps': self._default_config['fps'],
                },
                'motion_detection': {
                    'sensitivity': self._default_config['sensitivity'],
                    'motion_threshold': self._default_config['motion_threshold'],
                    'min_contour_area': self._default_config['min_contour_area'],
                    'motion_cooldown': self._default_config['motion_cooldown'],
                },
                'file_management': {
                    'images_dir': self._default_config['images_dir'],
                    'max_images': self._default_config['max_images'],
                    'image_format': self._default_config['image_format'],
                    'image_quality': self._default_config['image_quality'],
                },
                'system': {
                    'max_retries': self._default_config['max_retries'],
                    'retry_delay': self._default_config['retry_delay'],
                },
                'logging': {
                    'level': self._default_config['log_level'],
                    'file': self._default_config['log_file'],
                }
            }
            
            with open(self.config_path, 'w') as f:
                yaml.dump(config_data, f, default_flow_style=False, sort_keys=False)
                
            self.logger.info(f"Created default config at {self.config_path}")
            
        except Exception as e:
            self.logger.error(f"Failed to save default config: {e}")
            raise
            
    def get_image_save_params(self):
        """Return parameters for image saving."""
        return {
            'format': self.image_format.lower(),
            'quality': self.image_quality,
            'dir': str(self.images_dir),
            'max_retries': self.max_retries,
            'retry_delay': self.retry_delay
        }
        
    def __str__(self):
        """Safe string representation excluding sensitive info."""
        excluded = {'config_path'}
        items = []
        for k, v in self.__dict__.items():
            if not k.startswith('_') and k not in excluded:
                items.append(f"{k}: {v}")
        return "Configuration:\n" + "\n".join(f"  {item}" for item in sorted(items))