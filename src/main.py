from src.app_logger import LOG

def main():
    """
    Main entry point to launch the Gradio GUI.
    """
    LOG.info("Launching Personal Finance Agent GUI...")
    try:
        # We import here to avoid circular dependencies and to ensure
        # that the logger is initialized before other modules.
        from src.gui import demo
        demo.launch()
    except ImportError as e:
        LOG.error(f"Could not import Gradio interface: {e}")
        LOG.error("Please ensure Gradio is installed: pip install gradio")
    except Exception as e:
        LOG.error(f"An unexpected error occurred while launching the GUI: {e}")

if __name__ == '__main__':
    main()
