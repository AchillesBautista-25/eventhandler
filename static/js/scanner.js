(function () {
  // Read event ID from the DOM — no inline Jinja, no window global
  const qrReader = document.getElementById("qr-reader");
  if (!qrReader) return;

  const EVENT_ID   = qrReader.dataset.eventId;
  const resultBox  = document.getElementById("resultBox");
  const logList    = document.getElementById("logList");
  const logCount   = document.getElementById("logCount");
  const manualForm = document.getElementById("manualForm");
  const manualId   = document.getElementById("manualId");

  let currentCount = logList ? logList.children.length : 0;

  /* ---------- helpers ---------- */
  function showResult(ok, msg) {
    if (!resultBox) return;
    resultBox.classList.remove(
      "hidden", "bg-emerald-50", "text-emerald-800",
      "bg-rose-50", "text-rose-800"
    );
    resultBox.classList.add(
      ok ? "bg-emerald-50" : "bg-rose-50",
      ok ? "text-emerald-800" : "text-rose-800"
    );
    resultBox.textContent = msg;
  }

  function initialsOf(name) {
    return (name || "")
      .split(" ")
      .filter(Boolean)
      .map((p) => p[0])
      .join("")
      .slice(0, 2)
      .toUpperCase();
  }

  function prependLog(student) {
    if (!logList) return;
    const li = document.createElement("li");
    li.className =
      "flex items-center justify-between gap-3 p-3 rounded-xl bg-slate-50";
    li.innerHTML = `
      <div class="flex items-center gap-3 min-w-0">
        <div class="w-9 h-9 rounded-full bg-royal-100 text-royal-700 grid place-items-center text-xs font-bold shrink-0">
          ${initialsOf(student.name)}
        </div>
        <div class="min-w-0">
          <p class="text-sm font-semibold text-slate-800 truncate">${student.name}</p>
          <p class="text-xs text-slate-500">${student.school_id}</p>
        </div>
      </div>
      <div class="text-right shrink-0">
        <p class="text-xs font-semibold ${
          student.status === "LATE" ? "text-rose-600" : "text-emerald-600"
        }">${student.status}</p>
        <p class="text-xs text-slate-400">${student.time_in}</p>
      </div>`;
    logList.prepend(li);
    currentCount += 1;
    if (logCount) logCount.textContent = currentCount + " total";
  }

  /* ---------- check-in ---------- */
  async function checkIn(schoolId) {
    if (!schoolId || !EVENT_ID) return;
    try {
      const res = await fetch("/attendance/checkin", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ event_id: EVENT_ID, school_id: schoolId }),
      });
      const data = await res.json();

      if (data.ok) {
        showResult(true, "✅ " + data.message);
        prependLog(data.student);
        if (window.navigator.vibrate) window.navigator.vibrate(80);
      } else {
        showResult(false, "⚠️ " + data.message);
      }
    } catch (err) {
      showResult(false, "Network error — please try again.");
      console.error(err);
    }
  }

  /* ---------- manual form ---------- */
  if (manualForm && manualId) {
    manualForm.addEventListener("submit", (e) => {
      e.preventDefault();
      const id = manualId.value.trim();
      if (id) {
        checkIn(id);
        manualId.value = "";
        manualId.focus();
      }
    });
  }

  /* ---------- QR scanner ---------- */
  let scanner = null;
  const startBtn = document.getElementById("startScan");

  if (startBtn) {
    startBtn.addEventListener("click", async () => {
      if (scanner) return; // already running
      if (typeof Html5Qrcode === "undefined") {
        showResult(false, "QR library failed to load. Check your internet.");
        return;
      }
      scanner = new Html5Qrcode("qr-reader");
      try {
        await scanner.start(
          { facingMode: "environment" },
          { fps: 10, qrbox: 240 },
          (decodedText) => checkIn(decodedText.trim()),
          () => {} // per-frame decode errors — ignore
        );
        startBtn.textContent = "Scanning… point at a QR code";
        startBtn.disabled = true;
        startBtn.classList.add("opacity-60", "cursor-not-allowed");
      } catch (err) {
        showResult(false, "Camera unavailable: " + err);
        scanner = null;
      }
    });
  }
})();