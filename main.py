"""FPS practice tools built for CISC108 with Drafter."""

from dataclasses import dataclass
from math import isfinite
from drafter import (
    Page, Header, Paragraph, Button, TextBox, SelectBox, CheckBox, Label,
    Table, Link, Div, route, start_server, set_site_information,
    set_website_title, hide_debug_information, set_website_framed,
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


def navigation() -> list:
    """Build the same navigation on each of the six pages."""
    return [
        Button("Dashboard", index), Button("Add Training", add_session),
        Button("Training History", history), Button("Settings", settings),
        Button("Sensitivity Converter", converter), Button("Peripheral Finder", gear),
    ]


def page(state: State, title: str, content: list) -> Page:
    """Wrap content with navigation.

    The * syntax expands the component lists into one new list, in order.
    It does not copy mutable State or create global application data.
    """
    return Page(state, [Header("FPS Training Toolbox"), *navigation(),
                        Header(title, level=2), *content])


def field(caption: str, component: object) -> Div:
    """Render an accessible label alongside its actual input component."""
    return Div([Label(caption, component), component])


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
    content = [
        Paragraph("Game: " + state.selected_game),
        Paragraph(str(minutes) + " / " + str(state.practice_goal) + " practice minutes"),
    ]
    if count == 0:
        content.append(Paragraph("Your log for this game is empty. Add a training session to begin."))
    if minutes >= state.practice_goal:
        content.append(Paragraph("Goal reached! 0 minutes remaining."))
    else:
        content.append(Paragraph(str(state.practice_goal - minutes) + " minutes remaining."))
    rows = []
    for drill in drills:
        rows.append([drill, str(round(drills[drill][0] / drills[drill][1], 2)) + "%"])
    if rows:
        content.append(Table(rows, ["Drill", "Average accuracy"]))
    content.append(Paragraph("Compare accuracy only for the same drill and game. "
                             "Records stay in this browser app session."))
    return page(state, "Dashboard", content)


def training_form(state: State, game: str, drill: str, minutes: str,
                  accuracy: str, message: str) -> Page:
    """Render the training form and preserve entered values after errors."""
    return page(state, "Add Training", [
        Paragraph(message),
        field("Game", SelectBox("game", list(GAMES), game)),
        field("Drill", TextBox("drill", drill)),
        field("Minutes", TextBox("minutes", minutes)),
        field("Accuracy (%)", TextBox("accuracy", accuracy)),
        Button("Save Session", save_session),
    ])


@route
def add_session(state: State) -> Page:
    """Open an empty training form with the preferred game selected."""
    return training_form(state, state.selected_game, "", "", "", "Record completed practice.")


@route
def save_session(state: State, game: str, drill: str, minutes: str, accuracy: str) -> Page:
    """Add a validated session, then display the full history."""
    duration = whole_number(minutes)
    percentage = number(accuracy)
    if game not in GAMES or not drill.strip() or duration <= 0 or not 0 <= percentage <= 100:
        default_game = game
        if game not in GAMES:
            default_game = state.selected_game
        return training_form(state, default_game, drill, minutes, accuracy,
                             "Enter a drill, positive whole minutes, and accuracy from 0 to 100.")
    state.sessions.append(TrainingSession(game, drill.strip(), duration, percentage))
    return history(state)


def history_page(state: State, message: str) -> Page:
    """List all games and give each delete button its original list index."""
    content = [Paragraph(message)]
    if not state.sessions:
        content.append(Paragraph("No sessions yet. Add your first training session."))
    for position, session in enumerate(state.sessions):
        # enumerate supplies the exact list position as a hidden button argument.
        content.append(Paragraph(
            session.game + " / " + session.drill + " / " + str(session.minutes)
            + " min / " + str(session.accuracy) + "% accuracy"))
        content.append(Button("Delete Session", delete_session,
                              arguments={"session_index": position}))
    return page(state, "Training History", content)


@route
def history(state: State) -> Page:
    """Show the complete practice log for both supported games."""
    return history_page(state, "All recorded practice sessions")


@route
def delete_session(state: State, session_index: int) -> Page:
    """Delete the selected record only when its index is valid."""
    if session_index < 0 or session_index >= len(state.sessions):
        return history_page(state, "That session is unavailable. Choose an existing record.")
    state.sessions.pop(session_index)
    return history_page(state, "Session deleted.")


def settings_form(state: State, selected_game: str, practice_goal: str, message: str) -> Page:
    """Render preference controls and any validation message."""
    return page(state, "Settings", [
        Paragraph(message),
        field("Default game", SelectBox("selected_game", list(GAMES), selected_game)),
        field("Practice goal in minutes", TextBox("practice_goal", practice_goal)),
        Button("Save Settings", save_settings),
    ])


@route
def settings(state: State) -> Page:
    """Show the current game and practice goal."""
    return settings_form(state, state.selected_game, str(state.practice_goal),
                         "Set your practice target and dashboard game.")


@route
def save_settings(state: State, selected_game: str, practice_goal: str) -> Page:
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
    return page(state, "Sensitivity Converter", [
        Paragraph("CS2 and VALORANT default hip-fire settings at a shared DPI."),
        field("From game", SelectBox("source_game", list(GAMES), source_game)),
        field("To game", SelectBox("target_game", list(GAMES), target_game)),
        field("Shared mouse DPI", TextBox("dpi", dpi)),
        field("Source sensitivity", TextBox("source_sensitivity", source_sensitivity)),
        Button("Convert Sensitivity", convert_sensitivity),
        Paragraph(message),
        Paragraph("Matching cm/360 preserves turn distance. FOV and scoped settings affect visual feel."),
        Link("Conversion reference", "https://github.com/umut-hope/Yaw-Match"),
    ])


@route
def converter(state: State) -> Page:
    """Open the converter with a simple example."""
    return converter_form(state, "CS2", "VALORANT", "800", "1", "Enter settings and select Convert.")


@route
def convert_sensitivity(state: State, source_game: str, target_game: str,
                        dpi: str, source_sensitivity: str) -> Page:
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
    content = [
        Paragraph("A small comparison shortlist. Reference budgets in USD are fixed planning estimates."),
        field("Category", SelectBox("category", ["Mouse", "Mousepad"], category)),
        field("Budget ($)", TextBox("budget", budget)),
        field("Wireless mice only", CheckBox("wireless_only", wireless_only)),
        Button("Find Gear", filter_gear), Paragraph(message),
    ]
    matches = 0
    if show_results:
        for item in catalog():
            if item.category == category and item.price <= state.gear_budget:
                if category == "Mousepad" or not wireless_only or item.wireless:
                    matches += 1
                    content.extend([
                        Header(item.name, level=3),
                        Paragraph("$" + str(item.price) + " reference budget. " + item.reason),
                        Link("Manufacturer details", item.source),
                    ])
        if matches == 0:
            content.append(Paragraph("No matches. Try a larger budget or change the filters."))
    content.append(Paragraph("Catalog reviewed November 13, 2026. Check the manufacturer for current "
                             "prices, fit, and availability. Wireless applies to mice only."))
    return page(state, "Peripheral Finder", content)


@route
def gear(state: State) -> Page:
    """Open the finder with the previously saved budget."""
    return gear_form(state, "Mouse", str(state.gear_budget), False, "Choose your filters.", False)


@route
def filter_gear(state: State, category: str, budget: str, wireless_only: bool) -> Page:
    """Save a valid budget and display matching catalog items."""
    amount = number(budget)
    if category not in ("Mouse", "Mousepad") or not 0 <= amount <= 1000000:
        return gear_form(state, "Mouse", budget, wireless_only,
                         "Choose a category and enter a budget from 0 to 1000000.", False)
    state.gear_budget = amount
    return gear_form(state, category, budget, wireless_only, "Matching your saved budget", True)


set_website_title("FPS Training Toolbox")
set_site_information(
    author="Yibo Wang",
    description="Track FPS practice, match hip-fire sensitivity, and compare a small gear shortlist.",
    sources=["Drafter documentation", "https://github.com/umut-hope/Yaw-Match",
             "Manufacturer product pages linked in the gear finder",
             "Planning conversation in DRAFTER_PLANNING_CONVERSATION.md"],
    planning=["project0.docx", "project1.docx"],
    links=["https://github.com/liluno0308-source/fps-training-toolbox"],
)
hide_debug_information()
set_website_framed(False)
start_server(new_state())
