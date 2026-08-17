"""
cache_model.py — Pre-download and cache the SentenceTransformer embedding model.

This script ensures the 'all-MiniLM-L6-v2' model is downloaded and cached locally
before building the executable. This prevents runtime model downloads when the
executable starts, enabling fast, offline-first startup.

Usage:
    python cache_model.py

Environment:
    HF_HOME — Hugging Face cache directory (default: ~/.cache/huggingface)
    SENTENCE_TRANSFORMERS_HOME — SentenceTransformers cache (default: ~/.cache/sentence_transformers)
"""

import os
import sys
from pathlib import Path

def cache_model():
    """Download and cache the embedding model locally."""
    print("=" * 70)
    print("SentenceTransformer Model Caching")
    print("=" * 70)
    
    # Ensure model cache directory exists
    hf_home = Path.home() / ".cache" / "huggingface"
    st_home = Path.home() / ".cache" / "sentence_transformers"
    
    hf_home.mkdir(parents=True, exist_ok=True)
    st_home.mkdir(parents=True, exist_ok=True)
    
    print(f"\n📁 Hugging Face cache: {hf_home}")
    print(f"📁 SentenceTransformers cache: {st_home}")
    
    # Set environment variables for caching
    os.environ["HF_HOME"] = str(hf_home)
    os.environ["SENTENCE_TRANSFORMERS_HOME"] = str(st_home)
    
    print("\n⏳ Downloading 'all-MiniLM-L6-v2' model...")
    try:
        from sentence_transformers import SentenceTransformer
        
        model_name = "all-MiniLM-L6-v2"
        model = SentenceTransformer(model_name)
        
        print(f"✅ Model '{model_name}' cached successfully")
        print(f"   Model path: {model.get_sentence_embedding_dimension()}D embeddings")
        
        # Test the model with a sample sentence
        print("\n🧪 Testing model with sample sentence...")
        test_sentences = ["This is a test", "Another test sentence"]
        embeddings = model.encode(test_sentences, show_progress_bar=False)
        print(f"✅ Model inference works: {embeddings.shape}")
        
        print("\n" + "=" * 70)
        print("✨ Model caching complete! Ready for executable build.")
        print("=" * 70)
        return True
        
    except ImportError as e:
        print(f"❌ Error: SentenceTransformers not installed")
        print(f"   Install with: pip install sentence-transformers torch")
        print(f"   Details: {e}")
        return False
    except Exception as e:
        print(f"❌ Error downloading model: {e}")
        return False

if __name__ == "__main__":
    success = cache_model()
    sys.exit(0 if success else 1)
