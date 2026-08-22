"""Splash screen / player display route."""

import shutil
import subprocess

import flask_babel
from flask import jsonify, render_template
from flask_smorest import Blueprint

from pikaraoke.karaoke import Karaoke
from pikaraoke.lib.current_app import get_karaoke_instance, get_site_name
from pikaraoke.lib.raspi_wifi_config import get_raspi_wifi_text

_ = flask_babel.gettext


splash_bp = Blueprint("splash", __name__)


def _default_score_phrases() -> dict[str, list[str]]:
    """Translated built-in phrases, used when the user has not set custom ones."""
    return {
        "low": [
            _("Back to studying! Ban Bon Doi teachers need more practice! 📚"),
            _("Even the students at Ban Bon Doi gave that 1 star! ⭐"),
            _("The principal is calling a staff meeting about your singing! 🏫"),
            _("Ban Bon Doi birds flew away after hearing that! 🦜"),
            _("Recess is over... pass the mic! 🔔"),
        ],
        "mid": [
            _("Ban Bon Doi students approve... barely! 🎓"),
            _("Not bad teacher! You get a B+ for effort! 📝"),
            _("The whole school is vibrating from your vocals! 🏫"),
            _("Ban Bon Doi's finest karaoke teacher in training! 🎤"),
            _("Solid performance for staff room karaoke night! ☕"),
        ],
        "high": [
            _("Ban Bon Doi's #1 Teacher & Karaoke Legend! 🌟"),
            _("Give this teacher an A+ and a gold star! ⭐️👑"),
            _("The whole village of Ban Bon Doi is cheering for you! 📣"),
            _("Ban Bon Doi's next principal of Rock & Roll! 🎸"),
            _("Teacher of the Year award goes to this singer! 🏆"),
        ],
    }


def _parse_stored_phrases(stored: str) -> list[str]:
    """Split a stored phrase string on '|' (preferred) or '\\n' (legacy)."""
    sep = "|" if "|" in stored else "\n"
    return [p.strip() for p in stored.split(sep) if p.strip()]


def _get_active_score_phrases(k: Karaoke) -> dict[str, list[str]]:
    """Custom phrases if configured; translated built-in defaults otherwise."""
    defaults = _default_score_phrases()
    result = {}
    for tier in ("low", "mid", "high"):
        stored = getattr(k, f"{tier}_score_phrases")
        result[tier] = (_parse_stored_phrases(stored) if stored else []) or defaults[tier]
    return result


@splash_bp.route("/splash/score_phrases")
def get_score_phrases():
    """Active score phrases as JSON — translated defaults or user-defined custom phrases."""
    return jsonify(_get_active_score_phrases(get_karaoke_instance()))


@splash_bp.route("/splash")
def splash():
    """Splash screen / player display for TV output."""
    k = get_karaoke_instance()
    site_name = get_site_name()
    text = ""
    if k.is_raspberry_pi:
        has_iwconfig = shutil.which("iwconfig")
        has_iw = shutil.which("iw")
        if has_iwconfig or has_iw:
            # iwconfig is deprecated on Ubuntu, but still available on Raspbian
            command = "iwconfig" if has_iwconfig else "iw"
            status = subprocess.run([command, "wlan0"], stdout=subprocess.PIPE).stdout.decode(
                "utf-8"
            )
            if "Mode:Master" in status:
                # handle raspiwifi connection mode
                text = get_raspi_wifi_text()

    return render_template(
        "splash.html",
        site_title=site_name,
        blank_page=True,
        url=k.url,
        hostap_info=text,
        hide_url=k.hide_url,
        hide_session_name=k.hide_session_name,
        hide_logo=k.hide_logo,
        show_splash_clock=k.show_splash_clock,
        hide_overlay=k.hide_overlay,
        screensaver_timeout=k.screensaver_timeout,
        disable_bg_music=k.disable_bg_music,
        disable_bg_video=k.disable_bg_video,
        disable_score=k.disable_score,
        bg_music_volume=k.bg_music_volume,
        has_bg_video=k.bg_video_path is not None,
    )
