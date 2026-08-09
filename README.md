# chromecast-cli

A lightweight command-line tool to discover and control Chromecast devices on your local network — built for quick media control without opening a GUI app.

The tool supports:

- 🔎 **Scan** for available Chromecasts
- 📺 **Select** a device by name or index
- ▶️ **Play** (URL or pause/resume)
- ⏸️ **Pause / Stop**
- 🔊 **Volume** (get/set, up/down, mute)
- ⏩ **Seek** forward/backward
- 📼 **Now Playing** info (title, artist, album, etc.)

---

## 📦 Installation

```bash
git clone https://github.com/skuldexter-web/chromecast-cli.git
cd chromecast-cli
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

> On Kali you might need `pip3` or a virtual environment (recommended above) since system Python is often externally managed.

Make the script executable:

```bash
chmod +x cc.py
```

---

## 🚀 Usage Examples

```bash
# Discover devices
./cc.py scan

# Show status of first device found
./cc.py status

# Control a specific device by name (partial match) or index
./cc.py -d "Living" status
./cc.py -d 0 status

# Play a video/audio URL (must be reachable by the Chromecast)
./cc.py play "http://myserver.com/video.mp4"

# Force a content type if auto-detection guesses wrong
./cc.py play "http://myserver.com/stream" -c "audio/mpeg"

# Pause / Resume
./cc.py pause
./cc.py play

# Volume
./cc.py volume          # show volume
./cc.py volume 50       # set to 50%
./cc.py volup 5         # increase by 5%
./cc.py voldown         # decrease by 10% (default)
./cc.py mute
./cc.py unmute

# Seek to 30 seconds
./cc.py seek 30

# Show current media info
./cc.py now

# Stop & disconnect
./cc.py stop

# Adjust discovery timeout (default: 10s)
./cc.py -t 20 scan
```

---

## 🛠️ How It Works

- **Discovery** uses `pychromecast.get_chromecasts()`, which performs mDNS/DNS-SD discovery, and cleanly stops the background browser thread once devices are found.
- Devices are selected by **index** or **name** (case-insensitive substring match).
- Commands invoke the Chromecast's media controller and receiver methods directly.
- `cast.wait()` ensures the device connection is fully initialized before status is queried or commands are sent.
- Content type for `play` is guessed from the URL's file extension (via Python's `mimetypes`), with a `video/mp4` fallback and a `-c/--content-type` override flag.

---

## ⚠️ Notes & Tips

- Your machine must be on the **same network** as the Chromecast.
- The URL you play must be **reachable** by the Chromecast itself (both devices need network access to the media server).
- For **YouTube**, Netflix, etc., use their dedicated receiver apps — not supported directly here (that's a much more complex integration). This tool targets **castable URLs** (MP4, MP3, images, etc.).
- If you want app-specific controls (like YouTube), extend the script with `pychromecast.controllers.youtube`.
- If discovery finds nothing, double-check firewall rules — mDNS (UDP 5353) needs to be allowed on your network interface.

---

## 💡 Possible Extensions

- Queue multiple media items
- Support Chromecast groups (via `pychromecast.CastGroup`)
- Cache discovered devices between runs
- Integrate with system sound controls

---

## 📄 License

MIT — see [LICENSE](LICENSE).

---

*Built by SKULD — [skuldexter-web](https://github.com/skuldexter-web)*
