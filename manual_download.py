#!/usr/bin/env python3
"""
Manual download instructions for metamon pretrained models
"""

def show_manual_download_instructions():
    """Show manual download instructions"""
    
    print("=== MANUAL DOWNLOAD INSTRUCTIONS ===")
    print()
    print("If automatic download fails, you can manually download the models:")
    print()
    
    # Model definitions
    models = {
        "smallrl": {
            "name": "SmallRL",
            "size": "15M",
            "filename": "SmallRL.pt",
            "urls": [
                "https://huggingface.co/jakegrigsby/metamon/resolve/main/SmallRL.pt",
                "https://raw.githubusercontent.com/UT-Austin-RPL/metamon/main/models/SmallRL.pt",
                "https://github.com/UT-Austin-RPL/metamon/raw/main/models/SmallRL.pt"
            ]
        },
        "smallil": {
            "name": "SmallIL",
            "size": "15M", 
            "filename": "SmallIL.pt",
            "urls": [
                "https://huggingface.co/jakegrigsby/metamon/resolve/main/SmallIL.pt",
                "https://raw.githubusercontent.com/UT-Austin-RPL/metamon/main/models/SmallIL.pt",
                "https://github.com/UT-Austin-RPL/metamon/raw/main/models/SmallIL.pt"
            ]
        },
        "mediumrl": {
            "name": "MediumRL",
            "size": "50M",
            "filename": "MediumRL.pt",
            "urls": [
                "https://huggingface.co/jakegrigsby/metamon/resolve/main/MediumRL.pt",
                "https://raw.githubusercontent.com/UT-Austin-RPL/metamon/main/models/MediumRL.pt",
                "https://github.com/UT-Austin-RPL/metamon/raw/main/models/MediumRL.pt"
            ]
        },
        "mediumil": {
            "name": "MediumIL",
            "size": "50M",
            "filename": "MediumIL.pt", 
            "urls": [
                "https://huggingface.co/jakegrigsby/metamon/resolve/main/MediumIL.pt",
                "https://raw.githubusercontent.com/UT-Austin-RPL/metamon/main/models/MediumIL.pt",
                "https://github.com/UT-Austin-RPL/metamon/raw/main/models/MediumIL.pt"
            ]
        },
        "largerl": {
            "name": "LargeRL",
            "size": "200M",
            "filename": "LargeRL.pt",
            "urls": [
                "https://huggingface.co/jakegrigsby/metamon/resolve/main/LargeRL.pt",
                "https://raw.githubusercontent.com/UT-Austin-RPL/metamon/main/models/LargeRL.pt",
                "https://github.com/UT-Austin-RPL/metamon/raw/main/models/LargeRL.pt"
            ]
        },
        "largeil": {
            "name": "LargeIL",
            "size": "200M",
            "filename": "LargeIL.pt",
            "urls": [
                "https://huggingface.co/jakegrigsby/metamon/resolve/main/LargeIL.pt",
                "https://raw.githubusercontent.com/UT-Austin-RPL/metamon/main/models/LargeIL.pt",
                "https://github.com/UT-Austin-RPL/metamon/raw/main/models/LargeIL.pt"
            ]
        }
    }
    
    for model_key, model_info in models.items():
        print(f"--- {model_info['name']} ({model_info['size']}) ---")
        print(f"Model Key: {model_key}")
        print(f"Target File: models/{model_info['filename']}")
        print()
        print("Download Sources:")
        for i, url in enumerate(model_info['urls'], 1):
            print(f"  {i}. {url}")
        print()
        print("Download Commands:")
        print(f"  # Create models directory if needed")
        print(f"  mkdir -p models")
        print()
        print(f"  # Try with wget")
        print(f"  wget -O models/{model_info['filename']} '{model_info['urls'][0]}'")
        print()
        print(f"  # Or with curl")
        print(f"  curl -L -o models/{model_info['filename']} '{model_info['urls'][0]}'")
        print()
        print("After download, verify the file exists:")
        print(f"  ls -la models/{model_info['filename']}")
        print()
        print("---")
        print()
    
    print("=== HUGGING FACE HUB METHOD (RECOMMENDED) ===")
    print()
    print("1. Install huggingface-hub:")
    print("   pip install huggingface-hub")
    print()
    print("2. Download using Python:")
    print("   from huggingface_hub import hf_hub_download")
    print("   ")
    print("   # Download individual models")
    print("   hf_hub_download('jakegrigsby/metamon', 'SmallRL.pt', local_dir='models')")
    print("   hf_hub_download('jakegrigsby/metamon', 'SmallIL.pt', local_dir='models')")
    print("   hf_hub_download('jakegrigsby/metamon', 'MediumRL.pt', local_dir='models')")
    print("   hf_hub_download('jakegrigsby/metamon', 'MediumIL.pt', local_dir='models')")
    print("   hf_hub_download('jakegrigsby/metamon', 'LargeRL.pt', local_dir='models')")
    print("   hf_hub_download('jakegrigsby/metamon', 'LargeIL.pt', local_dir='models')")
    print()
    print("3. Or use the automatic CLI (preferred):")
    print("   pokeagent download --model smallrl")
    print("   pokeagent download --all")
    print()
    
    print("=== VERIFICATION ===")
    print()
    print("After downloading, verify models are available:")
    print("  pokeagent download --list")
    print()
    print("You should see ✅ instead of ❌ for downloaded models.")
    print()
    
    print("=== USAGE ===")
    print()
    print("Once models are downloaded, use them:")
    print("  pokeagent ladder --agent smallrl --battles 1")
    print("  pokeagent ladder --agent smallil --battles 1")
    print("  pokeagent ladder --agent mediumrl --battles 1")
    print("  pokeagent ladder --agent mediumil --battles 1")
    print("  pokeagent ladder --agent largerl --battles 1")
    print("  pokeagent ladder --agent largeil --battles 1")

if __name__ == "__main__":
    show_manual_download_instructions()