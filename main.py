"""FPS practice tools built for CISC108 with Drafter."""

from dataclasses import dataclass
from math import isfinite
from drafter import (
    Page, Header, Paragraph, Button, TextBox, SelectBox, CheckBox, Label,
    Table, Link, Div, route, start_server, set_site_information,
    set_website_title, hide_debug_information, set_website_framed,
    add_website_css_file, ProgressBar,
    set_website_style,
)


@dataclass
class TrainingSession:
    """One manually recorded practice session."""

    game: str
    drill: str
    minutes: int
    accuracy: float


@dataclass
class State:
    """Preferences and records shared by every page in this app session."""

    sessions: list[TrainingSession]
    practice_goal: int
    selected_game: str
    gear_budget: float


@dataclass
class GearOption:
    """A fixed catalog entry with a reference budget and source."""

    name: str
    category: str
    price: float
    wireless: bool
    reason: str
    source: str


GAMES = ("CS2", "VALORANT")
# Default hip-fire degrees per mouse count at sensitivity 1.
# Reference implementation https://github.com/umut-hope/Yaw-Match
CS2_YAW = 0.022
VALORANT_YAW = 0.07


def new_state() -> State:
    """Create an independent empty log with the planned defaults."""
    return State([], 60, "CS2", 75.0)


def box(content: list, class_name: str) -> Div:
    """Group components with a named CSS class.

    ** expands a dictionary into keyword arguments. This lets Python send the
    HTML attribute named class, which is otherwise a reserved Python keyword.
    The separate site.css file controls presentation, not application State.
    """
    return Div(content, **{"class": class_name})


def note(message: str, class_name: str = "hint") -> Paragraph:
    """Render a short message using a shared visual treatment."""
    attributes = {"class": class_name}
    if class_name == "error":
        attributes["role"] = "alert"
    elif class_name == "success":
        attributes["role"] = "status"
    return Paragraph(message, **attributes)


def action(label: str, target: object, kind: str = "primary",
           arguments: dict | None = None) -> Button:
    """Build a consistently styled real Drafter button, including arguments."""
    return Button(label, target, arguments=arguments, **{"class": "action " + kind})


def navigation(active: str) -> list:
    """Mark the current page and keep the same six navigation destinations."""
    destinations = [("Dashboard", index), ("Add Training", add_session),
                    ("Training History", history), ("Settings", settings),
                    ("Sensitivity Converter", converter), ("Peripheral Finder", gear)]
    buttons = []
    for label, target in destinations:
        attributes = {"class": "nav-button"}
        if label == active:
            attributes["class"] += " current"
            attributes["aria-current"] = "page"
        buttons.append(Button(label, target, **attributes))
    return buttons


def page(state: State, title: str, content: list) -> Page:
    """Wrap content with navigation.

    The * syntax expands the component lists into one new list, in order.
    It does not copy mutable State or create global application data.
    """
    descriptions = {
        "Dashboard": "Your practice, by game and drill.",
        "Add Training": "Keep a record of the work you put in.",
        "Training History": "Review your sessions across both games.",
        "Settings": "Set the game and goal you are working toward.",
        "Sensitivity Converter": "Carry your turn distance into another game.",
        "Peripheral Finder": "A small shortlist for your setup and budget.",
    }
    masthead = box([
        box([box([], "reticle"), Header("FPS Training Toolbox")], "brand"),
        note("CS2 + VALORANT", "game-tag"),
    ], "masthead")
    sidebar = box(navigation(title), "sidebar")
    sidebar.extra_settings.update({"role": "navigation", "aria-label": "Main navigation"})
    heading = box([Header(title, level=2), note(descriptions[title])], "page-heading")
    workspace = box([heading, box(content, "page-content")], "workspace")
    workspace.extra_settings["role"] = "main"
    footer = note("Session-only records. Reloading starts a new log.", "app-footer")
    return Page(state, [box([masthead, box([sidebar, workspace], "app-layout"),
                             footer], "app-shell")])


def field(caption: str, component: object, help_text: str = "") -> Div:
    """Render an accessible label alongside its actual input component."""
    component.extra_settings["aria-label"] = caption
    parts = [Label(caption, component), component]
    if help_text:
        help_id = component.get_id() + "-help"
        help_note = note(help_text, "field-help")
        help_note.extra_settings["id"] = help_id
        component.extra_settings["aria-describedby"] = help_id
        parts.append(help_note)
    name = "field"
    if isinstance(component, CheckBox):
        name += " field-check"
    return box(parts, name)


def prepare_static_metadata() -> None:
    """Avoid replaying unsupported metadata updates in Drafter 2.2.1.

    This is a framework compatibility workaround, beyond the CS1 material.
    set_site_information has already stored the metadata in the server's
    configuration. Drafter later replays its queued configuration events in
    Pyodide, but its browser bridge does not recognize the five metadata keys
    and reports a false synchronization error. The public event-bus queue is
    filtered before start_server: only those redundant metadata notifications
    are removed. Routes, State updates, and real error events remain intact.
    No installed library files or running browser handlers are changed.
    """
    from drafter.client_server.commands import get_main_server
    from drafter.data.details.config import UpdatedConfigurationEvent

    bus = get_main_server().event_bus
    remaining = []
    for event in bus.unprocessed_events:
        if isinstance(event, UpdatedConfigurationEvent):
            if event.key in ("author", "description", "sources", "planning", "links"):
                continue
        remaining.append(event)
    bus.unprocessed_events = remaining


def number(text: str) -> float:
    """Parse a finite decimal or return -1 for invalid input.

    Exception handling catches invalid numeric strings before they can crash
    a route. isfinite rejects NaN and infinity, which float() accepts.
    """
    try:
        value = float(text.strip())
    except (ValueError, OverflowError):
        return -1.0
    if not isfinite(value):
        return -1.0
    return value


def whole_number(text: str) -> int:
    """Parse positive ASCII whole numbers without accepting decimals."""
    clean = text.strip()
    if not clean or len(clean) > 9:
        return -1
    for character in clean:
        if character not in "0123456789":
            return -1
    return int(clean)


@route
def index(state: State) -> Page:
    """Summarize practice for the selected game and each matching drill.

    The local dictionary groups drills by name. Each value holds the accuracy
    total and entry count so different drills never share one average.
    """
    minutes = 0
    count = 0
    drills = {}
    for session in state.sessions:
        if session.game == state.selected_game:
            minutes += session.minutes
            count += 1
            if session.drill not in drills:
                drills[session.drill] = [0.0, 0]
            drills[session.drill][0] += session.accuracy
            drills[session.drill][1] += 1
    goal_content = [note("Game: " + state.selected_game, "game-tag"),
                    Header("Practice goal", level=3),
                    note(str(minutes) + " / " + str(state.practice_goal)
                         + " practice minutes", "goal-value"),
                    ProgressBar(min(minutes, state.practice_goal), max=state.practice_goal,
                                **{"aria-label": "Practice goal progress"})]
    if count == 0:
        goal_content.append(note("Your log for this game is empty. Add a training session to begin."))
    if minutes >= state.practice_goal:
        goal_content.append(note("Goal reached! 0 minutes remaining.", "success"))
    else:
        goal_content.append(note(str(state.practice_goal - minutes) + " minutes remaining."))
    goal_content.append(action("Add Training", add_session))
    content = [box(goal_content, "goal-panel")]
    rows = []
    for drill in drills:
        rows.append([drill, str(round(drills[drill][0] / drills[drill][1], 2)) + "%"])
    accuracy_content = [Header("Accuracy by drill", level=3)]
    if rows:
        accuracy_content.append(Table(rows, ["Drill", "Average accuracy"]))
    else:
        accuracy_content.append(note("No drill averages yet. Your first session will appear here."))
    accuracy_content.append(note("Compare accuracy only for the same drill and game.", "field-help"))
    content.append(box(accuracy_content, "data-section"))
    return page(state, "Dashboard", content)


def training_form(state: State, game: str, drill: str, minutes: str,
                  accuracy: str, message: str) -> Page:
    """Render the training form and preserve entered values after errors."""
    status = "hint"
    if message.startswith("Enter a drill"):
        status = "error"
    controls = [
        field("Game", SelectBox("game", list(GAMES), game)),
        field("Drill", TextBox("drill", drill, maxlength=80,
                              placeholder="e.g. Tracking or Flicking")),
        field("Minutes", TextBox("minutes", minutes, inputmode="numeric"), "Whole minutes, greater than 0"),
        field("Accuracy (%)", TextBox("accuracy", accuracy, inputmode="decimal"), "A value from 0 to 100"),
    ]
    return page(state, "Add Training", [box([
        note(message, status), box(controls, "form-grid"),
        box([action("Save Session", save_session), action("Cancel", index, "secondary")], "form-actions"),
    ], "form-panel")])


@route
def add_session(state: State) -> Page:
    """Open an empty training form with the preferred game selected."""
    return training_form(state, state.selected_game, "", "", "", "Record completed practice.")


@route
def save_session(state: State, game: str = "", drill: str = "",
                 minutes: str = "", accuracy: str = "") -> Page:
    """Add a validated session, then display the full history."""
    duration = whole_number(minutes)
    percentage = number(accuracy)
    if game not in GAMES or not 1 <= len(drill.strip()) <= 80 or duration <= 0 or not 0 <= percentage <= 100:
        default_game = game
        if game not in GAMES:
            default_game = state.selected_game
        return training_form(state, default_game, drill, minutes, accuracy,
                             "Enter a drill (1-80 characters), positive whole minutes, and accuracy from 0 to 100.")
    state.sessions.append(TrainingSession(game, drill.strip(), duration, percentage))
    return history(state)


def history_page(state: State, message: str, confirmation: int = -1) -> Page:
    """List all games and give each delete button its original list index."""
    content = [note(message, "success" if message == "Session deleted." else "hint")]
    if not state.sessions:
        content.append(box([Header("Your next session starts here", level=3),
                            note("No sessions yet. Add your first training session."),
                            action("Add Training", add_session)], "empty-state"))
    for position, session in enumerate(state.sessions):
        # enumerate supplies the exact list position as a hidden button argument.
        details = [note(session.game, "game-tag"), Header(session.drill, level=3),
                   Paragraph(str(session.minutes) + " min / " + str(session.accuracy) + "% accuracy")]
        controls = [action("Delete Session", confirm_delete, "danger-secondary",
                           {"session_index": position})]
        if confirmation == position:
            controls = [note("Delete this session? This removes it from the current log.", "error"),
                        action("Confirm Delete", delete_session, "danger", {"session_index": position}),
                        action("Keep Session", history, "secondary")]
        content.append(box([box(details, "session-details"), box(controls, "session-actions")], "session-row"))
    return page(state, "Training History", content)


@route
def history(state: State) -> Page:
    """Show the complete practice log for both supported games."""
    return history_page(state, "All recorded practice sessions")


@route
def confirm_delete(state: State, session_index: int = -1) -> Page:
    """Ask before deleting a session; viewing this prompt does not change State."""
    if session_index < 0 or session_index >= len(state.sessions):
        return history_page(state, "That session is unavailable. Choose an existing record.")
    return history_page(state, "Review the selected session before deleting.", session_index)


@route
def delete_session(state: State, session_index: int = -1) -> Page:
    """Delete the selected record only when its index is valid."""
    if session_index < 0 or session_index >= len(state.sessions):
        return history_page(state, "That session is unavailable. Choose an existing record.")
    state.sessions.pop(session_index)
    return history_page(state, "Session deleted.")


def settings_form(state: State, selected_game: str, practice_goal: str, message: str) -> Page:
    """Render preference controls and any validation message."""
    status = "error" if message.startswith("Choose a supported") else "hint"
    return page(state, "Settings", [box([
        note(message, status),
        box([field("Default game", SelectBox("selected_game", list(GAMES), selected_game)),
             field("Practice goal in minutes", TextBox("practice_goal", practice_goal, inputmode="numeric"),
                   "A positive whole-minute target for the selected game")], "form-grid"),
        box([action("Save Settings", save_settings), action("Cancel", index, "secondary")], "form-actions"),
    ], "form-panel")])


@route
def settings(state: State) -> Page:
    """Show the current game and practice goal."""
    return settings_form(state, state.selected_game, str(state.practice_goal),
                         "Set your practice target and dashboard game.")


@route
def save_settings(state: State, selected_game: str = "", practice_goal: str = "") -> Page:
    """Validate both preferences before updating either State field."""
    goal = whole_number(practice_goal)
    if selected_game not in GAMES or goal <= 0:
        return settings_form(state, state.selected_game, practice_goal,
                             "Choose a supported game and enter a positive whole-minute goal.")
    state.selected_game = selected_game
    state.practice_goal = goal
    return index(state)


def yaw(game: str) -> float:
    """Return the default hip-fire yaw for a validated supported game."""
    if game == "CS2":
        return CS2_YAW
    return VALORANT_YAW


def sensitivity_result(source_game: str, target_game: str,
                       dpi: int, source_sensitivity: float) -> list[float]:
    """Match physical turn distance while keeping the same mouse DPI."""
    target = source_sensitivity * yaw(source_game) / yaw(target_game)
    distance = 914.4 / (dpi * source_sensitivity * yaw(source_game))
    return [target, source_sensitivity * dpi, target * dpi, distance]


def converter_form(state: State, source_game: str, target_game: str,
                   dpi: str, source_sensitivity: str, message: str) -> Page:
    """Show conversion inputs and results together on one page."""
    controls = [
        field("From game", SelectBox("source_game", list(GAMES), source_game)),
        field("To game", SelectBox("target_game", list(GAMES), target_game)),
        field("Shared mouse DPI", TextBox("dpi", dpi, inputmode="numeric"), "Keep the same DPI in both games"),
        field("Source sensitivity", TextBox("source_sensitivity", source_sensitivity,
                                            inputmode="decimal")),
    ]
    result_content = [note(message)]
    result_class = "converter-note"
    if message.startswith("Target sensitivity:"):
        result_content = []
        for item in message.split("|"):
            label, value = item.split(":", 1)
            result_content.append(box([note(label.strip()), Header(value.strip(), level=3)], "result-item"))
        result_class = "conversion-results"
    elif message.startswith("Use whole DPI") or message.startswith("Choose"):
        result_content = [note(message, "error")]
    return page(state, "Sensitivity Converter", [box([
        note("CS2 and VALORANT default hip-fire settings at a shared DPI."),
        box(controls, "form-grid"), action("Convert Sensitivity", convert_sensitivity),
    ], "form-panel"), box(result_content, result_class),
        note("Matching cm/360 preserves turn distance. FOV and scoped settings affect visual feel.", "field-help"),
        Link("Conversion reference", "https://github.com/umut-hope/Yaw-Match"),
    ])


@route
def converter(state: State) -> Page:
    """Open the converter with a simple example."""
    return converter_form(state, "CS2", "VALORANT", "800", "1", "Enter settings and select Convert.")


@route
def convert_sensitivity(state: State, source_game: str = "CS2", target_game: str = "VALORANT",
                        dpi: str = "800", source_sensitivity: str = "1") -> Page:
    """Validate supported games and safe positive settings before conversion."""
    dots = whole_number(dpi)
    sensitivity = number(source_sensitivity)
    if source_game not in GAMES or target_game not in GAMES:
        return converter_form(state, "CS2", "VALORANT", dpi, source_sensitivity,
                              "Choose CS2 or VALORANT.")
    if not 1 <= dots <= 100000 or not 0.000001 <= sensitivity <= 10000:
        return converter_form(state, source_game, target_game, dpi, source_sensitivity,
                              "Use whole DPI from 1 to 100000 and sensitivity from 0.000001 to 10000.")
    values = sensitivity_result(source_game, target_game, dots, sensitivity)
    message = ("Target sensitivity: " + str(round(values[0], 6))
               + " | Source eDPI: " + str(round(values[1], 3))
               + " | Target eDPI: " + str(round(values[2], 3))
               + " | cm/360: " + str(round(values[3], 3)))
    return converter_form(state, source_game, target_game, dpi, source_sensitivity, message)


def catalog() -> list[GearOption]:
    """Return a fixed shortlist with reference budgets, not live store quotes."""
    return [
        GearOption("Logitech G305", "Mouse", 59.99, True,
                   "Wireless HERO-sensor mouse for a cable-free setup.",
                   "https://www.logitechg.com/en-us/shop/p/g305-lightspeed-wireless-gaming-mouse"),
        GearOption("Razer DeathAdder Essential", "Mouse", 29.99, False,
                   "Wired ergonomic mouse for a lower reference budget.",
                   "https://www.razer.com/gaming-mice/razer-deathadder-essential"),
        GearOption("Razer Gigantus V2 Medium", "Mousepad", 14.99, False,
                   "Cloth surface for controlled mouse movement.",
                   "https://www.razer.com/gaming-mouse-mats/razer-gigantus-v2"),
    ]


def gear_form(state: State, category: str, budget: str, wireless_only: bool,
              message: str, show_results: bool) -> Page:
    """Display filters and the fixed shortlist after a valid submission."""
    controls = [
        field("Category", SelectBox("category", ["Mouse", "Mousepad"], category)),
        field("Budget ($)", TextBox("budget", budget, inputmode="decimal")),
        field("Wireless mice only", CheckBox("wireless_only", wireless_only)),
    ]
    status = "error" if message.startswith("Choose a category") else "hint"
    content = [box([note("Reference budgets in USD are fixed planning estimates."),
                    box(controls, "form-grid gear-filters"), action("Find Gear", filter_gear)], "form-panel"),
               note(message, status)]
    matches = 0
    if show_results:
        for item in catalog():
            if item.category == category and item.price <= state.gear_budget:
                if category == "Mousepad" or not wireless_only or item.wireless:
                    matches += 1
                    content.append(box([
                        Header(item.name, level=3),
                        note("$" + str(item.price) + " reference budget", "reference-price"),
                        Paragraph(item.reason),
                        Link("Manufacturer details", item.source),
                    ], "gear-result"))
        if matches == 0:
            content.append(box([Header("Nothing in this budget yet", level=3),
                                note("No matches. Try a larger budget or change the filters.")], "empty-state"))
    content.append(note("Catalog reviewed November 13, 2026. Check the manufacturer for current "
                        "prices, fit, and availability. Wireless applies to mice only.", "field-help"))
    return page(state, "Peripheral Finder", content)


@route
def gear(state: State) -> Page:
    """Open the finder with the previously saved budget."""
    return gear_form(state, "Mouse", str(state.gear_budget), False, "Choose your filters.", False)


@route
def filter_gear(state: State, category: str = "Mouse", budget: str = "",
                wireless_only: bool = False) -> Page:
    """Save a valid budget and display matching catalog items."""
    amount = number(budget)
    if category not in ("Mouse", "Mousepad") or not 0 <= amount <= 1000000:
        return gear_form(state, "Mouse", budget, wireless_only,
                         "Choose a category and enter a budget from 0 to 1000000.", False)
    state.gear_budget = amount
    return gear_form(state, category, budget, wireless_only, "Matching your saved budget", True)


set_website_title("FPS Training Toolbox")
set_website_style("none")
add_website_css_file("site.css")
set_site_information(
    author="Yibo Wang",
    description="Track FPS practice, match hip-fire sensitivity, and compare a small gear shortlist.",
    sources=["Drafter documentation", "https://github.com/umut-hope/Yaw-Match",
             "Manufacturer product pages linked in the gear finder",
             "Planning conversation in DRAFTER_PLANNING_CONVERSATION.md"],
    planning=["project0.docx", "project1.docx"],
    links=["https://github.com/liluno0308-source/fps-training-toolbox"],
)
prepare_static_metadata()
hide_debug_information()
set_website_framed(False)
start_server(new_state())
