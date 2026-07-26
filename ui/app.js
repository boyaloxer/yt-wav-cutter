(() => {
  const $ = (id) => document.getElementById(id);

  const state = {
    mode: "audio",
    cutOn: false,
    downloading: false,
    lastError: "",
  };

  function parseHms(t) {
    const p = (t || "").split(":").map(Number);
    if (p.length !== 3 || p.some((n) => Number.isNaN(n))) return null;
    return p[0] * 3600 + p[1] * 60 + p[2];
  }

  function updateDuration() {
    const a = parseHms($("start").value);
    const b = parseHms($("end").value);
    const secs = a != null && b != null ? b - a : null;
    $("duration").textContent =
      secs != null && secs >= 0 ? `= ${secs} SEC` : "= ??";
  }

  function showCopyErr(show) {
    $("btn-copy-err").classList.toggle("hidden", !show);
    if (!show) {
      $("btn-copy-err").classList.remove("copied");
      $("btn-copy-err").textContent = "copy err";
    }
  }

  function setStatus(left, right, isError, fullError) {
    const el = $("status-left");
    el.textContent = left;
    el.title = isError ? fullError || left : "";
    el.classList.toggle("error", !!isError);
    $("status-right").textContent = right || "";
    if (isError) {
      state.lastError = fullError || left || "";
      showCopyErr(!!state.lastError);
    } else {
      state.lastError = "";
      showCopyErr(false);
    }
  }

  function setProgress(pct) {
    const n = Math.max(0, Math.min(100, Math.round(pct)));
    $("progress-fill").style.width = `${n}%`;
  }

  function setMode(mode) {
    state.mode = mode;
    document.querySelectorAll(".seg-btn").forEach((btn) => {
      btn.classList.toggle("active", btn.dataset.mode === mode);
    });
  }

  function setCutOn(on) {
    state.cutOn = on;
    $("cut-switch").setAttribute("aria-pressed", on ? "true" : "false");
    $("cut-panel").classList.toggle("hidden", !on);
  }

  // Called from Python
  window.__ytUpdate = function (payload) {
    if (!payload) return;
    if (typeof payload.progress === "number") {
      setProgress(payload.progress);
      const right = payload.speed
        ? `${Math.round(payload.progress)}% · ${payload.speed}`
        : `${Math.round(payload.progress)}%`;
      if (state.downloading) {
        $("status-right").textContent = right;
      }
    }
    if (payload.status) {
      const errText = payload.errorDetail || payload.status;
      setStatus(
        payload.status,
        $("status-right").textContent,
        !!payload.error,
        payload.error ? errText : ""
      );
    }
    if (payload.done) {
      state.downloading = false;
      $("btn-go").disabled = false;
      if (payload.error) {
        const errText = payload.errorDetail || payload.status || "ERROR";
        setStatus(payload.status || "ERROR", "FAIL", true, errText);
      } else {
        setProgress(100);
        const kind = state.mode === "audio" ? "WAV" : "MP4";
        setStatus(payload.status || `SAVED. ENJOY UR ${kind}`, "100%", false);
      }
    }
  };

  async function apiReady() {
    for (let i = 0; i < 80; i++) {
      if (window.pywebview && window.pywebview.api) return window.pywebview.api;
      await new Promise((r) => setTimeout(r, 50));
    }
    throw new Error("Python bridge not ready");
  }

  async function copyText(text) {
    if (!text) return false;
    try {
      const api = await apiReady();
      if (api.copy_clipboard) {
        const res = await api.copy_clipboard(text);
        if (res === true) return true;
        if (res && res.ok) return true;
      }
    } catch (e) {
      console.error("copy via python failed", e);
    }
    try {
      await navigator.clipboard.writeText(text);
      return true;
    } catch (e) {
      console.error("navigator.clipboard failed", e);
      return false;
    }
  }

  async function loadDeps() {
    try {
      const api = await apiReady();
      const d = await api.get_deps();
      const ff = $("chip-ffmpeg");
      const node = $("chip-node");
      const ytdlp = $("chip-ytdlp");

      ff.textContent = d.ffmpeg ? "FFMPEG OK" : "FFMPEG MISSING";
      ff.className = "chip" + (d.ffmpeg ? "" : " bad");
      ff.title = d.ffmpeg ? "ffmpeg found on PATH" : "Install ffmpeg and add it to PATH";

      const jsOk = d.js_ok;
      node.textContent = d.node ? "NODE OK" : d.deno ? "DENO OK" : "JS RUNTIME MISSING";
      node.className = "chip" + (jsOk ? "" : " bad");
      node.title = jsOk
        ? "JS runtime ready for yt-dlp"
        : "Install Node.js LTS for YouTube extraction";

      const ver = (d.yt_dlp || "?").replace(/^(\d+\.\d+).*/, "$1");
      ytdlp.textContent = `YT-DLP ${ver}`;
      ytdlp.className = "chip info";
    } catch (e) {
      console.error(e);
    }
  }

  $("btn-copy-err").addEventListener("click", async () => {
    const ok = await copyText(state.lastError);
    const btn = $("btn-copy-err");
    if (ok) {
      btn.textContent = "copied!";
      btn.classList.add("copied");
      setTimeout(() => {
        if (state.lastError) {
          btn.textContent = "copy err";
          btn.classList.remove("copied");
        }
      }, 1500);
    } else {
      btn.textContent = "copy fail";
    }
  });

  // Double-click status message also copies when it's an error
  $("status-left").addEventListener("dblclick", async () => {
    if (!state.lastError) return;
    const ok = await copyText(state.lastError);
    if (ok) setStatus($("status-left").textContent, "COPIED", true, state.lastError);
  });

  $("btn-paste").addEventListener("click", async () => {
    try {
      const api = await apiReady();
      const text = await api.paste_clipboard();
      if (text) $("url").value = text.trim();
    } catch (_) {
      try {
        const t = await navigator.clipboard.readText();
        if (t) $("url").value = t.trim();
      } catch (e) {
        setStatus("COULD NOT READ CLIPBOARD", "IDLE", true, String(e));
      }
    }
  });

  document.querySelectorAll(".seg-btn").forEach((btn) => {
    btn.addEventListener("click", () => setMode(btn.dataset.mode));
  });

  $("cut-switch").addEventListener("click", () => setCutOn(!state.cutOn));
  $("start").addEventListener("input", updateDuration);
  $("end").addEventListener("input", updateDuration);

  $("btn-go").addEventListener("click", async () => {
    if (state.downloading) return;
    const url = $("url").value.trim();
    if (!url) {
      setStatus("PASTE A URL FIRST", "IDLE", true, "Paste a YouTube URL first.");
      return;
    }
    if (state.cutOn) {
      const a = parseHms($("start").value);
      const b = parseHms($("end").value);
      if (a == null || b == null || b - a <= 0) {
        setStatus(
          "FIX START/END TIMES",
          "IDLE",
          true,
          "Start/end must be HH:MM:SS and end must be after start."
        );
        return;
      }
    }

    state.downloading = true;
    $("btn-go").disabled = true;
    setProgress(0);
    setStatus(
      state.mode === "audio" ? "DOWNLOADING AUDIO…" : "DOWNLOADING VIDEO…",
      "0%",
      false
    );

    try {
      const api = await apiReady();
      const result = await api.start_download({
        url,
        mode: state.mode,
        cutOn: state.cutOn,
        start: $("start").value.trim() || "00:00:00",
        end: $("end").value.trim(),
      });
      if (result && result.cancelled) {
        state.downloading = false;
        $("btn-go").disabled = false;
        setStatus("SAVE CANCELLED", "IDLE", false);
        setProgress(0);
      }
    } catch (e) {
      state.downloading = false;
      $("btn-go").disabled = false;
      setStatus(String(e), "FAIL", true, String(e));
    }
  });

  // Traffic-light window controls (frameless shell)
  function wireWindowControls() {
    const stopDrag = (el) => {
      if (!el) return;
      el.addEventListener("mousedown", (e) => e.stopPropagation());
    };
    ["btn-close", "btn-min", "btn-max"].forEach((id) => stopDrag($(id)));

    $("btn-close").addEventListener("click", async () => {
      try {
        const api = await apiReady();
        await api.window_close();
      } catch (_) {
        window.close();
      }
    });
    $("btn-min").addEventListener("click", async () => {
      try {
        const api = await apiReady();
        await api.window_minimize();
      } catch (_) {}
    });
    $("btn-max").addEventListener("click", async () => {
      try {
        const api = await apiReady();
        const res = await api.window_toggle_fullscreen();
        const on = !!(res && res.fullscreen);
        $("btn-max").title = on ? "Exit fullscreen" : "Fullscreen";
        $("btn-max").setAttribute("aria-label", on ? "Exit fullscreen" : "Fullscreen");
      } catch (_) {}
    });
  }

  setCutOn(false);
  updateDuration();
  wireWindowControls();
  window.addEventListener("pywebviewready", loadDeps);
  loadDeps();
})();
