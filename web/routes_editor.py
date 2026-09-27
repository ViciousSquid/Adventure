from __future__ import annotations

import json

from flask import jsonify, redirect, request, send_from_directory, session, url_for

from runtime.engine import AdventureEngine
from story.validator import StoryValidationError
from storage.package import PackageWriter


def _graph_data(story):
    nodes = [
        {"id": room_id, "label": room_id, "title": room.get("description", "")}
        for room_id, room in story.rooms.items()
    ]
    edges = []

    for room_id, room in story.rooms.items():
        for action_id, target in room.get("exits", {}).items():
            if isinstance(target, str):
                edges.append(
                    {"from": room_id, "to": target, "label": str(action_id).capitalize()}
                )
            elif isinstance(target, dict) and target.get("skill_check"):
                skill = target["skill_check"]
                success = skill.get("success", {}).get("room") or room_id
                failure = skill.get("failure", {}).get("room") or room_id
                edges.append({"from": room_id, "to": success, "label": f"{action_id} success"})
                edges.append({"from": room_id, "to": failure, "label": f"{action_id} failure"})

    return {"nodes": nodes, "edges": edges}


def register_editor_routes(app, services) -> None:
    @app.route("/editor")
    def editor_route():
        return send_from_directory("static/editor", "index.html")

    @app.route("/editor/stories")
    def stories_route():
        return jsonify(services.repository.list_stories())

    @app.route("/editor/edit")
    def edit_route():
        story_name = request.args.get("story")
        if not story_name:
            return redirect(url_for("editor_route"))
        return jsonify(services.repository.load(story_name).to_dict())

    @app.route("/editor/save", methods=["POST"])
    def save_route():
        story_data = request.form.get("story_data") or request.form.get("story")
        if not story_data:
            return jsonify({"error": "story_data is required"}), 400
        try:
            PackageWriter.build_zip(json.loads(story_data))
        except (json.JSONDecodeError, StoryValidationError, ValueError) as exc:
            return jsonify({"error": str(exc)}), 400
        return jsonify({"valid": True})

    @app.route("/editor/load")
    def load_route():
        story_name = request.args.get("story")
        if not story_name:
            return redirect(url_for("main_menu"))
        story = services.repository.load(story_name)
        state = AdventureEngine(story, story_id=story_name).new_game()
        session["game_state"] = state.to_dict()
        return redirect(url_for("adventure_game"))

    @app.route("/editor/graph")
    def graph_route():
        story_name = request.args.get("story")
        if not story_name:
            return jsonify({"error": "story query parameter is required"}), 400
        return jsonify(_graph_data(services.repository.load(story_name)))

    @app.route("/editor/generate_thumbnail", methods=["POST"])
    def generate_thumbnail_route():
        return "OK"
