# FPS Training Toolbox

Built by Yibo Wang for CISC108 using Drafter.

Track manual CS2 and VALORANT practice, convert default hip-fire sensitivity
at a shared DPI, and filter a small mouse and mousepad shortlist.

## Use the app

Start with Add Training. Select a game, enter a drill, positive whole minutes,
and an accuracy percentage from 0 to 100. History shows every session and lets
you delete entries. Settings changes the Dashboard game and practice goal.
The converter matches physical cm/360 using the default game factors.
Peripheral Finder saves your budget and applies category and wireless filters.

Records and preferences stay in the current app session.
Gear prices are fixed reference budgets for comparison. Check the source
product page for current offers and availability.

## Run and test

Install Python and Drafter with `python -m pip install drafter`.
Open `main.py` in Thonny and run it. Run `python test_main.py` for the tests.
The test file covers all eleven routes and invalid inputs.

## Planning and AI assistance

- [Project 0 worksheet](project0.docx)
- [Project 1 worksheet](project1.docx)
- [Drafter Planning Tool conversation](DRAFTER_PLANNING_CONVERSATION.md)

## Requirement mapping

- Six pages and eleven routes are defined in main.py.
- State has sessions, practice_goal, selected_game, and gear_budget.
- TrainingSession is the second dataclass. Saving and deleting changes its list.
- save_settings changes both the goal and selected game.
- filter_gear updates the saved budget.
- TextBox, SelectBox, and CheckBox collect user input.
- index loops through sessions and uses their attributes for totals and averages.
- Validation and empty-state branches provide meaningful conditions.
- Mutable application data is held in State. Global values are constants.
- All functions have type annotations and docstrings.
- set_site_information is configured in main.py.

## Sources

- [Drafter documentation](https://drafter-edu.github.io/drafter/)
- [Yaw-Match conversion formula and game data](https://github.com/umut-hope/Yaw-Match)
- Manufacturer sources are linked in the gear finder.
