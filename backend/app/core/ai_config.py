"""
CPU-optimized AI configuration for production deployments.
Reduces memory usage and Docker image size.
"""

import os
import torch
from typing import Optional

class CPUOptimizedConfig:
    """Configuration for CPU-only AI operations."""
    
    # Force CPU-only mode
    FORCE_CPU = True
    
    # PyTorch settings for CPU optimization
    TORCH_NUM_THREADS = int(os.getenv('TORCH_NUM_THREADS', '4'))
    OMP_NUM_THREADS = int(os.getenv('OMP_NUM_THREADS', '4'))
    
    # Model settings
    MODEL_MAX_LENGTH = 512  # Reduced for CPU efficiency
    BATCH_SIZE = 16  # Smaller batch for CPU
    
    # Sentence transformer settings
    SENTENCE_TRANSFORMER_CACHE = os.getenv('SENTENCE_TRANSFORMER_CACHE', '/app/models')
    
    @staticmethod
    def setup_cpu_optimization():
        """Setup CPU-only optimizations for AI models."""
        # Force CPU usage
        if CPUOptimizedConfig.FORCE_CPU:
            os.environ['CUDA_VISIBLE_DEVICES'] = ''
            torch.set_num_threads(CPUOptimizedConfig.TORCH_NUM_THREADS)
        
        # Optimize for inference
        torch.set_grad_enabled(False)
        
        # Set OpenMP threads
        os.environ['OMP_NUM_THREADS'] = str(CPUOptimizedConfig.OMP_NUM_THREADS)
        
        print(f"🔧 AI configured for CPU-only mode")
        print(f"📊 Torch threads: {CPUOptimizedConfig.TORCH_NUM_THREADS}")
        print(f"🎯 Batch size: {CPUOptimizedConfig.BATCH_SIZE}")

def get_device() -> str:
    """Get the appropriate device (always CPU in this config)."""
    return "cpu"

def load_model_cpu_optimized(model_name: str, cache_folder: Optional[str] = None):
    """Load model with CPU optimizations."""
    from sentence_transformers import SentenceTransformer
    
    # Setup CPU optimization
    CPUOptimizedConfig.setup_cpu_optimization()
    
    # Load model
    cache_folder = cache_folder or CPUOptimizedConfig.SENTENCE_TRANSFORMER_CACHE
    model = SentenceTransformer(
        model_name, 
        cache_folder=cache_folder,
        device='cpu'  # Force CPU
    )
    
    # Set to evaluation mode for inference
    model.eval()
    
    return model

# Export configuration
__all__ = [
    'CPUOptimizedConfig',
    'get_device', 
    'load_model_cpu_optimized'
]
