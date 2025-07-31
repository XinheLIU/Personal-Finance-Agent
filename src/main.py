from src.app_logger import LOG
from src.strategy import get_target_weights_and_metrics_standalone
from src.cache import TARGET_WEIGHTS_CACHE

def pre_calculate_target_weights():
    """
    Pre-calculates and caches the target weights on startup.
    """
    LOG.info("Pre-calculating target weights...")
    try:
        weights, reasoning = get_target_weights_and_metrics_standalone()
        if weights:
            TARGET_WEIGHTS_CACHE['weights'] = weights
            TARGET_WEIGHTS_CACHE['reasoning'] = reasoning
            LOG.info("Target weights calculated and cached successfully.")
        else:
            LOG.warning("Could not pre-calculate target weights. The cache is empty.")
    except Exception as e:
        LOG.error(f"Error during pre-calculation of target weights: {e}")

def main():
    """
    Main entry point to launch the Gradio GUI.
    """
    pre_calculate_target_weights()
    
    LOG.info("Launching Personal Finance Agent GUI...")
    try:
        from src.gui import demo
        demo.launch()
    except ImportError as e:
        LOG.error(f"Could not import Gradio interface: {e}")
        LOG.error("Please ensure Gradio is installed: pip install gradio")
    except Exception as e:
        LOG.error(f"An unexpected error occurred while launching the GUI: {e}")

if __name__ == '__main__':
    main()
