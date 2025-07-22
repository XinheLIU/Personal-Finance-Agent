# Instructions

During your interaction with the user, if you find anything reusable in this project (e.g. version of a library, model name), especially about a fix to a mistake you made or a correction you received, you should take note in the `Lessons` section in the `.cursorrules` file so you will not make the same mistake again. 

You should also use the 'GEMINI.md' file as a Scratchpad to organize your thoughts. Especially when you receive a new task, you should first review the content of the Scratchpad, clear old different task if necessary, first explain the task, and plan the steps you need to take to complete the task. You can use todo markers to indicate the progress, e.g.
[X] Task 1
[ ] Task 2

Also update the progress of the task in the Scratchpad when you finish a subtask.
Especially when you finished a milestone, it will help to improve your depth of task accomplishment to use the Scratchpad to reflect and plan.
The goal is to help you maintain a big picture as well as the progress of the task. Always refer to the Scratchpad when you plan the next step.

# Tools


# Lessons

## User Specified Lessons

- You have a conda env called 'py-fin' virural environment. Use it. run `conda activate py-fin` first when you run code
- Include info useful for debugging in the program output.
- Read the file before you try to edit it.
- Due to Cursor's limit, when you use `git` and `gh` and need to submit a multiline commit message, first write the message in a file, and then use `git commit -F <filename>` or similar command to commit. And then remove the file. Include "[Cursor] " in the commit message and PR title.

## GEMINI learned

- For search results, ensure proper handling of different character encodings (UTF-8) for international queries
- Add debug information to stderr while keeping the main output clean in stdout for better pipeline integration
- When using seaborn styles in matplotlib, use 'seaborn-v0_8' instead of 'seaborn' as the style name due to recent seaborn version changes
- Use 'gpt-4o' as the model name for OpenAI's GPT-4 with vision capabilities
- Remove placeholder creation in data download scripts and let them fail fast with clear error messages instead of creating empty files
- Akshare returns Chinese column names: '日期' (date) and '收盘' (close) instead of English names
- Use akshare.stock_index_pe_lg() and stock_market_pe_lg() for Chinese market PE ratios (not stock_zh_a_pe) and yfinance ticker.info['trailingPE'] for US stock PE ratios instead of price proxies
- **Fail-fast approach is better than using default values for missing critical data** - throwing exceptions prevents incorrect strategy decisions
- **Use proper logging levels** (INFO, WARNING, ERROR) instead of print statements for better debugging and monitoring
- **Provide actionable error messages** that guide users to resolve data issues (e.g., run data_download.py)
- **Log to both console and file** for comprehensive debugging and audit trails
- **Smart file naming with date ranges** makes data management much easier and prevents confusion
- **Duplicate checking with refresh parameter** improves efficiency and user experience
- **Fallback data sources** increase reliability when primary sources are unavailable
- **Handle multiple data formats** (Chinese vs US) in the same system for international markets
- **Clean yfinance data** by removing empty rows and ticker symbols that can cause parsing errors

# Scratchpad

## Current Task: README.md Update Completed ✅

### Task: Update README.md to reflect current code structure

**Completed Analysis:**
- ✅ Analyzed current modular architecture with `src/` directory structure
- ✅ Identified all key modules and their responsibilities:
  - `src/app_logger.py` - Logging configuration with loguru
  - `src/backtest_runner.py` - Backtesting orchestration 
  - `src/config.py` - Centralized configuration
  - `src/data_download.py` - Smart data management with date-range naming
  - `src/data_loader.py` - Data loading functionality
  - `src/main.py` - Simplified main entry point
  - `src/reporting.py` - Performance analysis & visualization
  - `src/strategy.py` - Strategy implementations
  - `src/strategy_utils.py` - Strategy utility functions
- ✅ Reviewed testing framework in `tests/` directory
- ✅ Understood smart data management features

**Major Updates Completed:**
- ✅ **Project Overview**: Updated to reflect modular architecture and smart data management
- ✅ **Key Features**: Added testing framework, smart data management with caching
- ✅ **Quick Start**: Updated with proper module imports (`python -m src.main`)
- ✅ **Architecture**: Completely rewritten to show modular design with each module's purpose
- ✅ **File Structure**: Updated to show actual current directory structure
- ✅ **Implementation Guide**: Updated examples to use framework utilities and proper imports
- ✅ **Smart Data Management**: Added section on intelligent caching and file naming
- ✅ **Testing Documentation**: Added comprehensive testing guide
- ✅ **Troubleshooting**: Updated for new architecture and common error patterns
- ✅ **Dependencies**: Updated to reflect current requirements

**Key Improvements Documented:**
- ✅ Modular `src/` directory structure for better organization
- ✅ Smart data management with date-range naming (e.g., `CSI300_price_20040101_to_20250715.csv`)
- ✅ Automatic caching that only downloads missing data periods  
- ✅ Centralized configuration through `config.py`
- ✅ Unit testing framework with pytest
- ✅ Enhanced error handling with fail-fast mechanisms
- ✅ Professional logging with loguru
- ✅ Strategy utility functions for reusable calculations

**README.md is now fully updated and accurately reflects the current sophisticated, modular architecture of the Personal Finance Agent framework.**
