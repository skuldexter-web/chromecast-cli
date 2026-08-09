#!/usr/bin/env python3
"""
Chromecast CLI - Discover, connect and control Chromecast devices.

Author: SKULD (skuldexter-web)
"""

import argparse
import mimetypes
import sys

try:
    import pychromecast
except ImportError:
    sys.exit(
        "pychromecast is not installed.\n"
        "Install it with: pip install pychromecast"
    )

DEFAULT_DISCOVERY_TIMEOUT = 10


def discover(show=True, timeout=DEFAULT_DISCOVERY_TIMEOUT):
    """Return a list of discovered Chromecast devices."""
    print("Searching for Chromecast devices...")
    try:
        casts, browser = pychromecast.get_chromecasts(timeout=timeout)
    except Exception as exc:  # noqa: BLE001 - surface any discovery failure cleanly
        sys.exit(f"Discovery failed: {exc}\nAre you on the same network as the device?")

    # Stop the mDNS browser thread cleanly once we have our results.
    try:
        pychromecast.discovery.stop_discovery(browser)
    except Exception:
        pass

    if show:
        if not casts:
            print("No Chromecast devices found.")
        for i, cast in enumerate(casts):
            print(f"[{i}] {cast.name} - {cast.host}:{cast.port}")
    return casts


def get_cast(args, casts=None):
    """Resolve the device to control based on --device or default to first found."""
    if casts is None:
        casts = discover(show=False)
    if not casts:
        sys.exit("No Chromecast devices found. Are you on the same network?")

    if args.device is not None:
        # Accept index or name
        if args.device.isdigit():
            idx = int(args.device)
            if idx >= len(casts):
                sys.exit(f"Device index {idx} not found. Only {len(casts)} available.")
            return casts[idx]
        else:
            for c in casts:
                if args.device.lower() in c.name.lower():
                    return c
            sys.exit(f"No Chromecast found with name containing '{args.device}'.")
    else:
        return casts[0]


def guess_content_type(url):
    """Best-effort content-type guess from a URL/file extension."""
    content_type, _ = mimetypes.guess_type(url)
    return content_type or "video/mp4"


def print_status(cast):
    """Wait for status update and print it."""
    cast.wait()
    print(f"Name: {cast.name}")
    print(f"Model: {cast.model_name}")
    print(f"Host: {cast.host}:{cast.port}")
    print(f"UUID: {cast.uuid}")

    print(f"Friendly Name: {cast.cast_info.friendly_name}")
    print(f"Cast Type: {cast.cast_info.cast_type}")
    print(f"Status: {cast.status.display_name}")
    print(f"Volume: {cast.status.volume_level:.0%} (muted: {cast.status.volume_muted})")

    if cast.media_controller.status and cast.media_controller.status.title is not None:
        ms = cast.media_controller.status
        print("\nCurrent Media:")
        print(f"  Title: {ms.title}")
        print(f"  Artist: {ms.artist}")
        print(f"  Album: {ms.album_name}")
        print(f"  Duration: {ms.duration} seconds")
        print(f"  Current time: {ms.current_time} seconds")
        print(f"  State: {ms.state}")
        print(f"  Player state: {ms.player_state}")
    else:
        print("No media currently playing.")


def safe_quit_app(cast):
    """Quit the running receiver app if one is active, without raising."""
    try:
        if cast.status and cast.status.app_id:
            cast.quit_app()
    except Exception as exc:  # noqa: BLE001
        print(f"Warning: could not quit app cleanly ({exc})")


def build_parser():
    parser = argparse.ArgumentParser(description="Control Chromecast devices from the CLI")
    parser.add_argument("-d", "--device", help="Device index or name (default: first found)")
    parser.add_argument(
        "-t", "--timeout", type=int, default=DEFAULT_DISCOVERY_TIMEOUT,
        help=f"Discovery timeout in seconds (default: {DEFAULT_DISCOVERY_TIMEOUT})"
    )
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    subparsers.add_parser("scan", help="List all discovered Chromecast devices")
    subparsers.add_parser("status", help="Show device and playback status")

    play_parser = subparsers.add_parser("play", help="Start a URL, or resume playback")
    play_parser.add_argument("url", nargs="?", help="Media URL to play (e.g., http://example.com/video.mp4)")
    play_parser.add_argument(
        "-c", "--content-type", help="Override content type (default: guessed from URL extension)"
    )

    subparsers.add_parser("pause", help="Pause current media")
    subparsers.add_parser("stop", help="Stop current media")

    vol_parser = subparsers.add_parser("volume", help="Get/Set volume (0-100)")
    vol_parser.add_argument("level", nargs="?", type=int, help="Volume level (0-100)")

    volup = subparsers.add_parser("volup", help="Increase volume")
    volup.add_argument("delta", nargs="?", type=int, default=10, help="Increase amount (default: 10)")

    voldown = subparsers.add_parser("voldown", help="Decrease volume")
    voldown.add_argument("delta", nargs="?", type=int, default=10, help="Decrease amount (default: 10)")

    subparsers.add_parser("mute", help="Mute audio")
    subparsers.add_parser("unmute", help="Unmute audio")

    seek_parser = subparsers.add_parser("seek", help="Seek to a position in seconds")
    seek_parser.add_argument("position", type=int, help="Target position in seconds")

    subparsers.add_parser("now", help="Show current media info")
    subparsers.add_parser("quit", help="Stop current media and disconnect")

    return parser


def main():
    parser = build_parser()
    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(0)

    if args.level if hasattr(args, "level") else False:
        if args.level is not None and not (0 <= args.level <= 100):
            sys.exit("Volume level must be between 0 and 100.")

    if args.command == "scan":
        discover(timeout=args.timeout)
        return

    casts = discover(show=False, timeout=args.timeout)
    cast = get_cast(args, casts)

    cast.wait()
    mc = cast.media_controller

    try:
        if args.command == "status":
            print_status(cast)

        elif args.command == "play":
            if args.url:
                content_type = args.content_type or guess_content_type(args.url)
                mc.play_media(args.url, content_type)
                mc.block_until_active(timeout=10)
                print(f"Playing: {args.url} ({content_type})")
            else:
                mc.play()
                print("Playback resumed.")

        elif args.command == "pause":
            mc.pause()
            print("Paused.")

        elif args.command == "stop":
            mc.stop()
            safe_quit_app(cast)
            print("Stopped and app closed.")

        elif args.command == "volume":
            if args.level is not None:
                cast.set_volume(args.level / 100.0)
                print(f"Volume set to {args.level}%")
            else:
                print(f"Volume: {cast.status.volume_level:.0%}")
                print(f"Muted: {cast.status.volume_muted}")

        elif args.command == "volup":
            new_vol = cast.status.volume_level + args.delta / 100.0
            cast.set_volume(min(1.0, new_vol))
            cast.wait()
            print(f"Volume up -> {cast.status.volume_level:.0%}")

        elif args.command == "voldown":
            new_vol = cast.status.volume_level - args.delta / 100.0
            cast.set_volume(max(0.0, new_vol))
            cast.wait()
            print(f"Volume down -> {cast.status.volume_level:.0%}")

        elif args.command == "mute":
            cast.set_volume_muted(True)
            print("Muted.")

        elif args.command == "unmute":
            cast.set_volume_muted(False)
            print("Unmuted.")

        elif args.command == "seek":
            if not mc.status or mc.status.player_state == "IDLE":
                sys.exit("No active media to seek.")
            mc.seek(args.position)
            print(f"Seeked to {args.position} seconds.")

        elif args.command == "now":
            ms = mc.status
            if ms and ms.title is not None:
                print(f"Title: {ms.title}")
                print(f"Artist: {ms.artist}")
                print(f"Album: {ms.album_name}")
                print(f"Duration: {ms.duration}s")
                print(f"Current: {ms.current_time}s")
                print(f"State: {ms.state}")
            else:
                print("No media playing.")

        elif args.command == "quit":
            mc.stop()
            safe_quit_app(cast)
            print("Player stopped.")

    finally:
        cast.disconnect()


if __name__ == "__main__":
    main()
