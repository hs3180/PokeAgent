import logging
import os
import shutil
import sys
from pathlib import Path
from typing import Dict, List, Optional

# Try to import huggingface-hub
try:
    from huggingface_hub import hf_hub_download
    HUGGINGFACE_HUB_AVAILABLE = True
except ImportError:
    HUGGINGFACE_HUB_AVAILABLE = False


logger = logging.getLogger(__name__)

# Available pretrained models - Hugging Face only
PRETRAINED_MODELS = {
    "smallrl": {
        "name": "SmallRL",
        "description": "15M parameter RL model (latest epoch 40)",
        "size": "15M",
        "repo_id": "jakegrigsby/metamon",
        "filename": "small-rl/ckpts/policy_weights/policy_epoch_40.pt"
    },
    "smallil": {
        "name": "SmallIL", 
        "description": "15M parameter IL model (latest epoch 46)",
        "size": "15M",
        "repo_id": "jakegrigsby/metamon",
        "filename": "small-il/ckpts/policy_weights/policy_epoch_46.pt"
    },
    "mediumrl": {
        "name": "MediumRL",
        "description": "50M parameter RL model (latest epoch 40)", 
        "size": "50M",
        "repo_id": "jakegrigsby/metamon",
        "filename": "medium-rl/ckpts/policy_weights/policy_epoch_40.pt"
    },
    "mediumil": {
        "name": "MediumIL",
        "description": "50M parameter IL model (latest epoch 96)",
        "size": "50M", 
        "repo_id": "jakegrigsby/metamon",
        "filename": "medium-il/ckpts/policy_weights/policy_epoch_96.pt"
    },
    "largerl": {
        "name": "LargeRL",
        "description": "200M parameter RL model (latest epoch 50)",
        "size": "200M",
        "repo_id": "jakegrigsby/metamon",
        "filename": "large-rl/ckpts/policy_weights/policy_epoch_50.pt"
    },
    "largeil": {
        "name": "LargeIL",
        "description": "200M parameter IL model (latest epoch 50)",
        "size": "200M",
        "repo_id": "jakegrigsby/metamon",
        "filename": "large-il/ckpts/policy_weights/policy_epoch_50.pt"
    }
}


class ModelDownloader:
    """Handle downloading pretrained models"""
    
    def __init__(self, models_dir: str = "models"):
        self.models_dir = Path(models_dir)
        self.models_dir.mkdir(exist_ok=True)
    
    def list_available_models(self) -> Dict[str, Dict]:
        """List all available pretrained models"""
        return PRETRAINED_MODELS
    
    def list_downloaded_models(self) -> List[str]:
        """List already downloaded models"""
        if not self.models_dir.exists():
            return []
        
        downloaded = []
        for file in self.models_dir.glob("*.pt"):
            downloaded.append(file.stem)
        return downloaded
    
    def download_model(self, model_name: str, force: bool = False) -> bool:
        """Download a specific model using huggingface-hub"""
        model_key = model_name.lower()
        
        if model_key not in PRETRAINED_MODELS:
            logger.error(f"Unknown model: {model_name}")
            logger.info(f"Available models: {', '.join(PRETRAINED_MODELS.keys())}")
            return False
        
        model_info = PRETRAINED_MODELS[model_key]
        # Create a clean filename from the model key
        clean_filename = f"{model_info['name']}.pt"
        target_path = self.models_dir / clean_filename
        
        # Check if model already exists
        if target_path.exists() and not force:
            logger.info(f"Model {model_name} already exists at {target_path}")
            logger.info("Use --force to overwrite")
            return True
        
        # Check if huggingface-hub is available
        if not HUGGINGFACE_HUB_AVAILABLE:
            logger.error("huggingface-hub is required for model downloads")
            logger.info("Install it with: pip install huggingface-hub")
            return False
        
        logger.info(f"Downloading {model_info['name']} ({model_info['size']}) from Hugging Face...")
        
        # Download using huggingface-hub
        try:
            success = self._download_with_huggingface(model_info, target_path, force)
            if success:
                return True
        except Exception as e:
            logger.error(f"Download failed: {e}")
        
        logger.error(f"❌ Failed to download {model_name}")
        logger.info("Please check:")
        logger.info("1. huggingface-hub is installed: pip install huggingface-hub")
        logger.info("2. Internet connection is working")
        logger.info("3. Model exists on Hugging Face: jakegrigsby/metamon")
        return False
    
    def _download_with_huggingface(self, model_info: dict, target_path: Path, force: bool) -> bool:
        """Download model using huggingface-hub"""
        try:
            logger.info(f"Downloading from Hugging Face: {model_info['repo_id']}/{model_info['filename']}")
            
            # Download using huggingface-hub
            downloaded_path = hf_hub_download(
                repo_id=model_info["repo_id"],
                filename=model_info["filename"],
                local_dir=self.models_dir,
                local_files_only=False,
                force_download=force
            )
            
            # Verify the file was downloaded correctly
            if Path(downloaded_path).exists() and Path(downloaded_path).stat().st_size > 0:
                logger.info(f"✅ Successfully downloaded using huggingface-hub")
                logger.info(f"Saved to: {downloaded_path}")
                
                # If the file is not at the expected location, move it
                if str(downloaded_path) != str(target_path):
                    shutil.move(str(downloaded_path), str(target_path))
                    logger.info(f"Moved to: {target_path}")
                
                return True
            else:
                logger.warning("huggingface-hub download resulted in empty file")
                return False
                
        except Exception as e:
            logger.error(f"huggingface-hub download error: {e}")
            return False
    
    def download_all_models(self, force: bool = False) -> Dict[str, bool]:
        """Download all available models"""
        logger.info("Downloading all available models...")
        
        results = {}
        for model_name in PRETRAINED_MODELS.keys():
            logger.info(f"\n--- Downloading {model_name} ---")
            results[model_name] = self.download_model(model_name, force)
        
        # Show summary
        logger.info("\n=== Download Summary ===")
        success_count = sum(1 for result in results.values() if result)
        total_count = len(results)
        
        for model_name, success in results.items():
            status = "✅" if success else "❌"
            logger.info(f"{status} {model_name}")
        
        logger.info(f"\nSuccessfully downloaded {success_count}/{total_count} models")
        return results
    
    def show_model_info(self):
        """Show information about available models"""
        print("=== Available Pretrained Models ===")
        print()
        
        downloaded = self.list_downloaded_models()
        
        for model_key, model_info in PRETRAINED_MODELS.items():
            status = "✅" if model_info["name"] in downloaded else "❌"
            print(f"{status} {model_key.upper()}")
            print(f"    Name: {model_info['name']}")
            print(f"    Size: {model_info['size']}")
            print(f"    Description: {model_info['description']}")
            print(f"    Filename: {model_info['filename']}")
            print(f"    Repository: {model_info['repo_id']}")
            print()
        
        print("=== Requirements ===")
        if HUGGINGFACE_HUB_AVAILABLE:
            print("✅ huggingface-hub is installed and ready")
        else:
            print("❌ huggingface-hub is required")
            print("   Install with: pip install huggingface-hub")
        print()
        
        print("=== Download Method ===")
        print("All models are downloaded exclusively via huggingface-hub")
        print("from the jakegrigsby/metamon repository")
        print()
        
        print("=== Usage ===")
        print("After downloading, use with:")
        print("  pokeagent ladder --agent smallrl --battles 1")
        print("  pokeagent ladder --agent smallil --battles 1")
        print("  pokeagent ladder --agent mediumrl --battles 1")
        print("  etc.")


def download_model_command(args):
    """Handle download model command"""
    downloader = ModelDownloader(args.models_dir)
    
    if args.list:
        downloader.show_model_info()
        return
    
    if args.all:
        downloader.download_all_models(args.force)
        return
    
    if args.model:
        downloader.download_model(args.model, args.force)
    else:
        downloader.show_model_info()