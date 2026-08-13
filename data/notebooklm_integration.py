import asyncio
import os
import logging
from pathlib import Path
from typing import Optional
from huggingface_hub import hf_hub_download
from huggingface_hub.utils import HfHubHTTPError

try:
    from notebooklm import NotebookLMClient
except ImportError:
    NotebookLMClient = None

logger = logging.getLogger(__name__)

class ModelPodcastGenerator:
    """
    Integrates with NotebookLM to generate deep-dive audio podcasts 
    for HuggingFace models based on their Model Cards (README.md).
    """
    
    def __init__(self, output_dir: str = "outputs/podcasts"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
    def _download_hf_readme(self, model_id: str) -> Optional[Path]:
        """Downloads the README.md (Model Card) for a given HuggingFace model."""
        try:
            readme_path = hf_hub_download(repo_id=model_id, filename="README.md")
            return Path(readme_path)
        except HfHubHTTPError as e:
            logger.error(f"Failed to download README for {model_id}: {e}")
            return None
        except Exception as e:
            logger.error(f"Error fetching {model_id} model card: {e}")
            return None

    async def generate_podcast(self, model_id: str, instructions: str = "Focus on the technical architecture, benchmarks, and best use cases for this AI model.") -> Optional[Path]:
        """
        Creates a NotebookLM notebook, uploads the model card, 
        and generates an audio podcast discussing the model.
        """
        if NotebookLMClient is None:
            raise ImportError("notebooklm-py is not installed. Run: pip install notebooklm-py[browser]")
            
        logger.info(f"Fetching Model Card for {model_id}...")
        readme_path = self._download_hf_readme(model_id)
        
        if not readme_path:
            raise ValueError(f"Could not retrieve README.md for {model_id}.")
            
        # Clean up model_id for filename (replace / with _)
        safe_model_id = model_id.replace("/", "_")
        output_file = self.output_dir / f"{safe_model_id}_deep_dive.m4a"
        
        if output_file.exists():
            logger.info(f"Podcast already exists at {output_file}")
            return output_file
            
        logger.info(f"Connecting to NotebookLM...")
        # NotebookLMClient.from_storage() automatically uses cookies saved by `notebooklm login`
        async with NotebookLMClient.from_storage() as client:
            notebook_name = f"ModelRank: {safe_model_id}"
            logger.info(f"Creating notebook: '{notebook_name}'")
            nb = await client.notebooks.create(notebook_name)
            
            logger.info(f"Uploading model card to notebook {nb.id}...")
            await client.sources.add_file(nb.id, str(readme_path), wait=True)
            
            logger.info(f"Generating audio podcast (this may take a few minutes)...")
            status = await client.artifacts.generate_audio(nb.id, instructions=instructions)
            
            # Wait for generation to complete
            await client.artifacts.wait_for_completion(nb.id, status.task_id)
            
            logger.info(f"Downloading podcast to {output_file}...")
            await client.artifacts.download_audio(nb.id, str(output_file))
            
            logger.info("Done! Podcast generated successfully.")
            return output_file

def generate_podcast_sync(model_id: str):
    """Synchronous wrapper for CLI usage."""
    generator = ModelPodcastGenerator()
    return asyncio.run(generator.generate_podcast(model_id))

if __name__ == "__main__":
    import sys
    # Quick CLI testing: python -m data.notebooklm_integration mistralai/Mistral-7B-v0.1
    if len(sys.argv) > 1:
        model = sys.argv[1]
        logging.basicConfig(level=logging.INFO)
        result = generate_podcast_sync(model)
        print(f"\\n🔊 Podcast ready: {result}")
    else:
        print("Usage: python -m data.notebooklm_integration <hf_model_id>")
