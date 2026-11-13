# Drafter Planning Tool conversation

Tool: Drafter Planning Tool (V2.0.0b1), by Austin C Bart.
Date: November 13, 2026.
Conversation: https://chatgpt.com/g/g-6a6276313a9c8191af1f065698f516bf/c/6af77c94-2304-83ea-8028-c75acb502032

## User

I am building an FPS Training Toolbox with Drafter for CISC108. It has six pages: Dashboard, Add Training, History, Settings, Sensitivity Converter, and Peripheral Finder. State has sessions: list[TrainingSession], practice_goal: int, selected_game: str, and gear_budget: float. TrainingSession has game, drill, minutes, and accuracy. What is a simple way to organize the page routes, action routes, and helper functions? How should I validate text inputs before changing State, and what should I test before GitHub Pages deployment? Please answer briefly in English without writing implementation code.

## Drafter Planning Tool

For your CISC108 FPS Training Toolbox, I recommend organizing the program into **three main sections: page routes, action routes, and helper functions**. Keep everything in one Python file initially to make debugging easier.

### 1. Page routes

Create one page route for each of your six pages:

| Page | Responsibility |
| --- | --- |
| Dashboard | Display total practice time, average accuracy, and progress toward the goal |
| Add Training | Show a form for entering a training session |
| History | Display previously recorded sessions |
| Settings | Change practice goal and selected game |
| Sensitivity Converter | Convert mouse sensitivity between games |
| Peripheral Finder | Suggest equipment based on budget |

Each page should read information from State and display it without unnecessarily changing data.

### 2. Action routes

Action routes respond to user interactions.

- **Save Training:** Validate inputs and append a new TrainingSession to sessions.
- **Update Settings:** Save a valid practice goal and selected game.
- **Convert Sensitivity:** Calculate and display the converted sensitivity.
- **Find Peripherals:** Filter a predefined equipment list using gear_budget.

Keep calculations in helper functions instead of repeating them across routes.

### 3. Helper functions

Useful helpers include:

- calculate_total_minutes — Adds all training minutes.
- calculate_average_accuracy — Computes average accuracy and handles an empty history.
- calculate_goal_progress — Compares practice time with the goal.
- validate_training_input — Checks submitted session information.
- convert_sensitivity — Uses predefined conversion factors.
- filter_peripherals — Finds equipment within the budget.

### 4. Input validation

**Always validate text before updating State.**

| Input | Validation |
| --- | --- |
| Game | Must be a supported game |
| Drill | Must not be empty |
| Minutes | Must be a positive integer |
| Accuracy | Must be a number between 0 and 100 |
| Practice goal | Must be a positive integer |
| Gear budget | Must be a nonnegative number |
| Sensitivity | Must be a positive number |

Remove extra whitespace, check that numeric conversions are possible, and display a helpful error message for invalid entries.

**Important:** Do not modify State if validation fails. Preserve the user's previous data.

### 5. Testing before GitHub Pages deployment

Test these scenarios:

- [ ] All six pages open and navigation works.
- [ ] Valid training sessions save and appear in History.
- [ ] Empty, negative, and nonnumeric inputs produce helpful errors.
- [ ] Dashboard calculations work with zero sessions and multiple sessions.
- [ ] Settings changes update the appropriate State fields.
- [ ] Sensitivity conversions produce expected results.
- [ ] Peripheral Finder handles budgets with no matching products.
- [ ] Refreshing the page behaves as intended.
- [ ] LocalStorage saves and restores data correctly, if implemented.
- [ ] The deployed application works in a browser without relying on a Python backend.

Remember that **Drafter runs in the browser using Pyodide**. GitHub Pages can host the application, but it does not provide a backend database. Use LocalStorage if you want training sessions to persist after refreshing. Test that storage behavior in the deployed version.

### Final recommendation

For a first-year CS project, prioritize **working navigation, reliable training-session tracking, and correct calculations** before adding advanced features.

Build Dashboard, Add Training, and History first. Then implement Settings, Sensitivity Converter, and Peripheral Finder using simple predefined game and equipment data.

This keeps the project manageable while demonstrating routes, dataclasses, lists, validation, state management, and helper functions.
