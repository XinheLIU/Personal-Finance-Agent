# Instructions

During your interaction with the user, if you find anything reusable in this project (e.g. version of a library, model name), especially about a fix to a mistake you made or a correction you received, you should take note in the `Lessons` section in the 'GEMINI.md' file so you will not make the same mistake again. 

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
- Read the file before you try to edit it. record your understanding of this repo in GEMINI.md.
- Use GEMINI.md as a draft box to complete your task.
- execute step by step, using GEMINI.md as a draft.


## GEMINI learned

### principles

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

### Project info


# Scratchpad

## Current Task: Refactor for Extensibility and Add Features

### Plan

[X] **Phase 1: Code Analysis and Initial Refactoring**
    [X] Read key files (`main.py`, `gui.py`, `strategy.py`, `backtest_runner.py`, `config.py`)
    [X] Understand current strategy implementation and execution flow.
    [X] Formulate a detailed implementation plan.

[X] **Phase 2: Add Built-in Strategies**
    [X] Check `config.py` for available assets.
    [X] Implement fixed-weight strategies in `src/strategy.py`:
        [X] 60/40 Portfolio
        [X] Permanent Portfolio
        [X] All Weather Portfolio
        [X] David Swensen's Portfolio
    [X] Verify existing Buy and Hold strategy.

[X] **Phase 3: Separate GUI and CLI modes**
    [X] Refactor `src/main.py` to accept a `--mode` argument (`gui` or `cli`).
    [X] Consolidate `backtest_runner.py` logic into the `cli` mode in `main.py`.

[X] **Phase 4: GUI Enhancements**
    [X] Add UI in `src/gui.py` for creating custom fixed-weight strategies.
    [X] Add a "Download Data" button that executes `data_download.py`.

[X] **Phase 5: Documentation**
    [X] Update `README.md` with new features and instructions.
    [X] Update `CHANGELOG.md` with a new version entry.
