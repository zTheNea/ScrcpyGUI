"""Pure function to build scrcpy command-line arguments from a config dict.

This module is independent of the GUI framework so it can be unit-tested
without importing customtkinter.
"""
from datetime import datetime


def _safe_int(value, default=0):
    """Safely convert a value to int, returning *default* on failure."""
    try:
        return int(value)
    except (ValueError, TypeError):
        return default


def build_scrcpy_args(cfg, is_windows=True):
    """Build a list of scrcpy CLI arguments from a flat config dictionary.

    Parameters
    ----------
    cfg : dict
        Flat key→value mapping.  Expected keys mirror the ``v_<key>`` tkinter
        variables in ScrcpyGUI (without the ``v_`` prefix).  All values should
        already be plain Python types (str, int, bool).
    is_windows : bool
        Whether the host OS is Windows (controls V4L2 visibility).

    Returns
    -------
    list[str]
        The argument list (without the scrcpy executable itself).
    """
    args = []

    # ── Device ──────────────────────────────────────
    dev = str(cfg.get("device", "")).split(" (")[0]
    if dev and "Buscando" not in dev and "Sin dispositivos" not in dev:
        args.extend(["-s", dev])

    # ── OTG shortcut ────────────────────────────────
    if cfg.get("otg_mode"):
        args.append("--otg")
        return args

    # ── No-video ────────────────────────────────────
    if cfg.get("no_video"):
        args.append("--no-video")

    # ── Video Source ────────────────────────────────
    src = str(cfg.get("video_source", "display"))
    if src == "camera":
        args.append("--video-source=camera")
        if cfg.get("camera_torch"):
            args.append("--camera-torch")
        zoom = str(cfg.get("camera_zoom", "")).strip()
        if zoom:
            args.append(f"--camera-zoom={zoom}")
        cid = str(cfg.get("camera_id", "0")).strip()
        if cid and cid != "0":
            args.append(f"--camera-id={cid}")
        else:
            facing = str(cfg.get("camera_facing", ""))
            if facing:
                args.append(f"--camera-facing={facing}")
        cam_fps = _safe_int(cfg.get("camera_fps", 30), 30)
        if cam_fps and cam_fps != 30:
            args.append(f"--camera-fps={cam_fps}")
    else:
        ms = str(cfg.get("max_size", "")).strip()
        if ms and ms != "0":
            args.append(f"--max-size={ms}")
        did = str(cfg.get("display_id", "0")).strip()
        if did and did != "0":
            args.append(f"--display-id={did}")

    codec = str(cfg.get("codec", "h264"))
    if codec and codec != "h264":
        args.append(f"--video-codec={codec}")
    fps = _safe_int(cfg.get("fps", 0))
    if fps:
        args.append(f"--max-fps={fps}")
    br = _safe_int(cfg.get("bitrate", 8), 8)
    if br and br != 8:
        args.append(f"--video-bit-rate={br}M")

    # ── Orientation ─────────────────────────────────
    orient = str(cfg.get("orientation", "0"))
    if orient and orient != "0":
        args.append(f"--orientation={orient}")

    # ── Audio ───────────────────────────────────────
    if not cfg.get("audio", True):
        args.append("--no-audio")
    else:
        audio_src = str(cfg.get("audio_source", "output"))
        if audio_src != "output":
            args.append(f"--audio-source={audio_src}")
        ac = str(cfg.get("audio_codec", "opus"))
        if ac != "opus":
            args.append(f"--audio-codec={ac}")
        ab = _safe_int(cfg.get("audio_buf", 0))
        if ab > 0:
            args.append(f"--audio-buffer={ab}")
        abr = _safe_int(cfg.get("audio_bitrate", 128), 128)
        if abr != 128:
            args.append(f"--audio-bit-rate={abr}K")
        if cfg.get("audio_dup"):
            args.append("--audio-dup")

    # ── Video buffer ────────────────────────────────
    vb = _safe_int(cfg.get("video_buffer", 0))
    if vb > 0:
        args.append(f"--video-buffer={vb}")

    # ── Window ──────────────────────────────────────
    if cfg.get("fullscreen"):
        args.append("--fullscreen")
    if cfg.get("always_on_top"):
        args.append("--always-on-top")
    if cfg.get("borderless"):
        args.append("--window-borderless")
    if cfg.get("disable_screensaver"):
        args.append("--disable-screensaver")
    if not cfg.get("otg_mode"):
        if cfg.get("stay_awake"):
            args.append("--stay-awake")
        if cfg.get("screen_off"):
            args.append("--turn-screen-off")
        if cfg.get("keep_active"):
            args.append("--keep-active")
    bg = str(cfg.get("background_color", "")).strip()
    if bg:
        args.append(f"--background-color={bg}")
    if cfg.get("no_aspect_ratio_lock"):
        args.append("--no-window-aspect-ratio-lock")

    # ── Virtual Display ─────────────────────────────
    if cfg.get("virtual_display") and src != "camera":
        res = str(cfg.get("virtual_display_res", "1280x720")).strip() or "1280x720"
        dpi = str(cfg.get("virtual_dpi", "")).strip()
        vd_val = f"{res}/{dpi}" if dpi else res
        args.append(f"--new-display={vd_val}")
        if cfg.get("flex_display"):
            args.append("--flex-display")
        v_app = str(cfg.get("virtual_display_app", "")).strip()
        if v_app:
            args.append(f"--start-app={v_app}")
        if cfg.get("no_vd_decorations"):
            args.append("--no-vd-system-decorations")
        if cfg.get("no_vd_destroy"):
            args.append("--no-vd-destroy-content")

    if not is_windows:
        v4l2 = str(cfg.get("v4l2_device", "")).strip()
        if v4l2:
            args.append(f"--v4l2-sink={v4l2}")

    # ── Controls ────────────────────────────────────
    if cfg.get("no_control") or src == "camera":
        args.append("--no-control")
    else:
        kb = str(cfg.get("keyboard", ""))
        if kb and kb != "sdk":
            args.append(f"--keyboard={kb}")
        ms2 = str(cfg.get("mouse", ""))
        if ms2 and ms2 != "sdk":
            args.append(f"--mouse={ms2}")
        gp = str(cfg.get("gamepad", ""))
        if gp:
            args.append(f"--gamepad={gp}")

    if cfg.get("no_clipboard_sync"):
        args.append("--no-clipboard-autosync")

    # ── Recording ───────────────────────────────────
    if cfg.get("record"):
        rf = str(cfg.get("record_file", "recording.mp4")).strip() or "recording.mp4"
        rf = datetime.now().strftime(rf)
        args.append(f"--record={rf}")
    tl = _safe_int(cfg.get("time_limit", 0))
    if tl > 0:
        args.append(f"--time-limit={tl}")

    if cfg.get("print_fps"):
        args.append("--print-fps")
    if cfg.get("show_touches"):
        args.append("--show-touches")
    crop = str(cfg.get("crop", "")).strip()
    if crop and src != "camera":
        args.append(f"--crop={crop}")

    return args
