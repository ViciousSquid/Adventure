from __future__ import annotations

import base64

from flask import jsonify, redirect, render_template, request, send_from_directory, session, url_for


def register_main_routes(app, services) -> None:
    @app.route("/", methods=["GET", "POST"])
    def main_menu():
        adventures = services.repository.list_stories()

        if request.method == "POST":
            selected_story = request.form.get("story_name")
            return redirect(url_for("play_story", story_name=selected_story))

        selected_story = request.args.get("story_name")
        if session.get("story_uploaded"):
            uploaded = session.pop("story_uploaded")
            return redirect(url_for("play_story", story_name=uploaded))

        if not selected_story or selected_story not in adventures:
            selected_story = next(iter(adventures), None)

        cover_image_data = None
        summary_text = None
        if selected_story:
            try:
                cover_image_data = services.repository.read_asset(selected_story, "cover.jpg")
                summary_text = services.repository.read_text_asset(selected_story, "summary.txt")
            except FileNotFoundError:
                pass

        user_agent = request.headers.get("User-Agent", "")
        mobile = ("Android", "iPhone", "iPad", "iPod", "BlackBerry", "Windows Phone")
        template_name = "main_menu_mobile.html" if any(k in user_agent for k in mobile) else "main_menu.html"

        return render_template(
            template_name,
            adventures=adventures,
            selected_story=selected_story,
            cover_image_data=cover_image_data,
            summary_text=summary_text,
        )

    @app.route("/fonts/<path:filename>")
    def serve_fonts(filename):
        return send_from_directory("fonts", filename)

    @app.route("/get_story_data")
    def get_story_data():
        story_name = request.args.get("story_name")
        if not story_name:
            return jsonify({"error": "story_name is required"}), 400

        try:
            cover = services.repository.read_asset(story_name, "cover.jpg")
        except FileNotFoundError:
            cover = None

        return jsonify(
            {
                "cover_image_data": base64.b64encode(cover).decode("ascii") if cover else None,
                "summary_text": services.repository.read_text_asset(story_name, "summary.txt"),
            }
        )
