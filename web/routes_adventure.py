from __future__ import annotations

import json
from pathlib import Path

from flask import jsonify, make_response, redirect, render_template, request, session, url_for
from werkzeug.utils import secure_filename

from dicerollAPI.diceroll_anim import DiceAnimator
from runtime.dice import DiceEngine
from runtime.engine import AdventureEngine
from runtime.state import GameState

from .presentation import render_markup


def _state_and_engine(services):
    payload = session.get("game_state")
    if not payload:
        return None, None
    state = GameState.from_dict(payload)
    story = services.repository.load(state.story_name)
    return state, AdventureEngine(story, trace=services.trace_enabled, story_id=state.story_name)


def _save_state(state: GameState) -> None:
    session["game_state"] = state.to_dict()
    session.modified = True


def _start_story(services, story_name: str):
    story = services.repository.load(story_name)
    engine = AdventureEngine(story, trace=services.trace_enabled, story_id=story_name)
    state = engine.new_game()
    _save_state(state)
    return state, engine


def _render_game(services, state, engine, result=None, item_message=""):
    result = result or engine.observe(state)
    story = engine.story
    room = story.room(state.current_room)

    animation_html = ""
    dice_notation = ""
    player_roll = None
    if result.dice_results:
        dice = result.dice_results[-1]
        player_roll = dice.to_dict()
        dice_notation = dice.expression
        animation_html = DiceAnimator().animate_dice_roll_html(
            dice.expression, "blue", dice.to_dict()
        )

    roll_dice_button = ""
    if result.awaiting_roll:
        roll_dice_button = (
            '<form method="post">'
            '<button type="submit" name="roll_dice" id="roll-dice-button">Roll Dice</button>'
            "</form>"
        )

    return render_template(
        "adventure.html",
        content=render_markup(result.text),
        exits=[
            (choice["id"], story.room(state.current_room)["exits"][choice["id"]])
            for choice in result.choices
        ],
        room=room,
        show_map=room.get("show_map", True),
        action_history=state.history_rooms,
        button_color=story.data.get("button_color", "#4CAF50"),
        story_title=story.name,
        skill_check=None,
        player_roll=player_roll,
        animation_html=animation_html,
        roll_dice_button=roll_dice_button,
        dice_notation=dice_notation,
        player_inventory=list(state.inventory),
        available_items=engine.available_items(state),
        item_needed=room.get("item_needed"),
        room_message=room.get("message"),
        item_message=item_message,
        zip_contents=services.repository.package_members(state.story_name),
    )


def register_adventure_routes(app, services) -> None:
    @app.route("/images/<path:filename>")
    def serve_image(filename):
        state, engine = _state_and_engine(services)
        if not state:
            return redirect(url_for("main_menu"))
        room = engine.story.room(state.current_room)
        if room.get("image") != filename:
            return redirect(url_for("main_menu"))
        try:
            data = services.repository.read_asset(state.story_name, filename)
        except FileNotFoundError:
            return redirect(url_for("main_menu"))
        response = make_response(data)
        response.headers.set("Content-Type", "image/jpeg")
        return response

    @app.route("/new_story", methods=["GET", "POST"])
    def new_story():
        story_name = request.args.get("story_name") or request.form.get("story_name")
        if session.get("story_uploaded"):
            story_name = session.pop("story_uploaded")
        if not story_name:
            return redirect(url_for("main_menu"))
        try:
            _start_story(services, story_name)
        except (FileNotFoundError, ValueError) as exc:
            return render_template("error.html", error=str(exc)), 400
        return redirect(url_for("adventure_game"))

    @app.route("/adventure", methods=["GET", "POST"])
    def adventure_game():
        state, engine = _state_and_engine(services)
        if not state:
            return redirect(url_for("main_menu"))

        result = None
        if request.method == "POST":
            if request.form.get("roll_dice"):
                result = engine.step(state, "roll")
            else:
                action = request.form.get("direction")
                result = engine.step(state, action) if action else engine.observe(state)
            _save_state(state)

        return _render_game(
            services,
            state,
            engine,
            result=result,
            item_message=request.args.get("item_message", ""),
        )

    @app.route("/play")
    def play_story():
        story_name = request.args.get("story_name")
        if story_name:
            state, engine = _start_story(services, story_name)
        else:
            state, engine = _state_and_engine(services)
            if not state:
                return redirect(url_for("main_menu"))

        result = engine.observe(state)
        room = engine.story.room(state.current_room)
        return render_template(
            "play.html",
            adventure=engine.story.to_dict(),
            current_room=state.current_room,
            action_history=state.history_rooms,
            content=render_markup(result.text),
            exits=[choice["id"] for choice in result.choices],
            room_image=room.get("image"),
        )

    @app.route("/play_action", methods=["POST"])
    def play_action():
        state, engine = _state_and_engine(services)
        if not state:
            return redirect(url_for("main_menu"))
        result = engine.step(state, request.form.get("direction", ""))
        _save_state(state)
        room = engine.story.room(state.current_room)
        return render_template(
            "play.html",
            adventure=engine.story.to_dict(),
            current_room=state.current_room,
            action_history=state.history_rooms,
            content=render_markup(result.text),
            exits=[choice["id"] for choice in result.choices],
            room_image=room.get("image"),
        )

    @app.route("/roll", methods=["POST"])
    def roll_dice():
        expression = request.form.get("dice_notation", "1d20")
        try:
            result = DiceEngine().roll(
                expression,
                target=request.form.get("target_value", type=int),
            )
        except ValueError as exc:
            return jsonify({"error": str(exc)}), 400
        animation_html = DiceAnimator().animate_dice_roll_html(
            expression, "blue", result.to_dict()
        )
        return jsonify(
            {
                "animation_html": animation_html,
                "roll_result": str(result.total),
                "dice": result.to_dict(),
            }
        )

    @app.route("/dice_roll_image")
    def serve_dice_roll_image():
        return '<img src="" alt="Dice Roll Animation">'

    @app.route("/save", methods=["POST"])
    def save_game():
        state, engine = _state_and_engine(services)
        if not state:
            return redirect(url_for("main_menu"))
        payload = json.dumps(state.to_dict(), indent=2).encode("utf-8")
        response = make_response(payload)
        response.headers.set("Content-Type", "application/json")
        response.headers.set(
            "Content-Disposition", "attachment", filename="game_state.json"
        )
        return response

    @app.route("/load", methods=["POST"])
    def load_game():
        uploaded = request.files.get("file")
        if uploaded is None:
            return redirect(url_for("main_menu"))
        try:
            data = json.load(uploaded.stream)
            state = GameState.from_dict(data)
            services.repository.load(state.story_name)
        except (ValueError, json.JSONDecodeError, FileNotFoundError) as exc:
            return render_template("error.html", error=str(exc)), 400
        _save_state(state)
        return redirect(url_for("adventure_game"))

    @app.route("/acquire_item", methods=["POST"])
    def acquire_item():
        state, engine = _state_and_engine(services)
        if not state:
            return redirect(url_for("main_menu"))
        result = engine.acquire_item(state, request.form.get("item_name", ""))
        _save_state(state)
        return redirect(url_for("adventure_game", item_message=result.text))

    @app.route("/use_item", methods=["POST"])
    def use_item():
        state, engine = _state_and_engine(services)
        if not state:
            return redirect(url_for("main_menu"))
        result = engine.use_item(state, request.form.get("item_name", ""))
        _save_state(state)
        return redirect(url_for("adventure_game", item_message=result.text))

    @app.route("/upload_story", methods=["POST"])
    def upload_story():
        story_file = request.files.get("story_file")
        if not story_file or not story_file.filename:
            return redirect(url_for("main_menu"))

        filename = secure_filename(story_file.filename)
        if not filename.lower().endswith(".zip"):
            return redirect(url_for("main_menu"))

        destination = Path(services.repository.root) / filename
        destination.parent.mkdir(parents=True, exist_ok=True)
        story_file.save(destination)

        try:
            services.repository.invalidate()
            services.repository.load_path(destination)
        except (ValueError, OSError) as exc:
            destination.unlink(missing_ok=True)
            return render_template("error.html", error=str(exc)), 400

        session["story_uploaded"] = destination.stem
        services.repository.invalidate(destination.stem)
        return redirect(url_for("main_menu"))
