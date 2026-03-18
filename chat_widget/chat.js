// ── Markdown config ──────────────────────────────────────────────
marked.setOptions({ breaks: true, gfm: true });

// ── DOM refs ─────────────────────────────────────────────────────
const toggle = document.getElementById("chat-toggle");
const container = document.getElementById("chat-container");
const closeBtn = document.getElementById("close-btn");
const clearBtn = document.getElementById("clear-btn");
const expandBtn = document.getElementById("expand-btn");
const sendBtn = document.getElementById("send-btn");
const input = document.getElementById("user-input");
const chatWindow = document.getElementById("chat-window");
const typing = document.getElementById("typing");

const sessionId = "stay-" + Math.random().toString(36).substring(2, 9);

// ── Toggle ───────────────────────────────────────────────────────
toggle.onclick = () => {
  container.classList.toggle("active");
  // Exit fullscreen when closing
  if (!container.classList.contains("active")) {
    container.classList.remove("fullscreen");
  }
};
closeBtn.onclick = () => {
  container.classList.remove("active");
  container.classList.remove("fullscreen");
};
clearBtn.onclick = () => {
  chatWindow.innerHTML = '<div class="date-divider">Today</div>';
  setTimeout(() => addMsg("Chat cleared. How can I assist you?", "bot"), 300);
};

// ── Fullscreen Toggle ────────────────────────────────────────────
expandBtn.onclick = () => {
  container.classList.toggle("fullscreen");
  const isFS = container.classList.contains("fullscreen");
  expandBtn.title = isFS ? "Exit fullscreen" : "Expand to fullscreen";
  chatWindow.scrollTo({ top: chatWindow.scrollHeight });
};

// Escape key exits fullscreen
document.addEventListener("keydown", (e) => {
  if (e.key === "Escape" && container.classList.contains("fullscreen")) {
    container.classList.remove("fullscreen");
    expandBtn.title = "Expand to fullscreen";
  }
});

// ── Time helper ──────────────────────────────────────────────────
function now() {
  const d = new Date();
  let h = d.getHours(),
    m = String(d.getMinutes()).padStart(2, "0");
  const ap = h >= 12 ? "PM" : "AM";
  h = h % 12 || 12;
  return h + ":" + m + " " + ap;
}

// ── Render message ───────────────────────────────────────────────
function addMsg(text, sender) {
  const msg = document.createElement("div");
  msg.classList.add("msg", sender);

  const avatar = document.createElement("div");
  avatar.classList.add("msg-avatar", sender);
  if (sender === "bot") {
    avatar.innerHTML = `<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="color:#c9a86c"><path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/><polyline points="9 22 9 12 15 12 15 22"/></svg>`;
  } else {
    avatar.innerHTML = `<svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="color:#a78bfa"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>`;
  }

  const body = document.createElement("div");
  body.classList.add("msg-body");

  const bubble = document.createElement("div");
  bubble.classList.add("msg-bubble", sender);

  if (sender === "bot") {
    bubble.innerHTML = marked.parse(text);
  } else {
    bubble.textContent = text;
  }

  const time = document.createElement("div");
  time.classList.add("msg-time");
  time.textContent = now();

  body.appendChild(bubble);
  body.appendChild(time);
  msg.appendChild(avatar);
  msg.appendChild(body);
  chatWindow.appendChild(msg);
  chatWindow.scrollTo({ top: chatWindow.scrollHeight, behavior: "smooth" });
}

// ── Quick send ───────────────────────────────────────────────────
function quick(text) {
  getBotResponse(text);
}

// ── API call (unchanged) ─────────────────────────────────────────
async function getBotResponse(text) {
  if (!text.trim()) return;
  addMsg(text, "user");
  input.value = "";
  typing.classList.add("show");
  chatWindow.scrollTo({ top: chatWindow.scrollHeight, behavior: "smooth" });

  try {
    const res = await fetch("http://127.0.0.1:8000/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ session_id: sessionId, message: text }),
    });
    const data = await res.json();
    typing.classList.remove("show");
    addMsg(extract(data), "bot");
  } catch {
    typing.classList.remove("show");
    addMsg(
      "**Connection Error**\n\nUnable to reach the backend. Please check that the server is running at `http://127.0.0.1:8000`.",
      "bot"
    );
  }
}

function extract(data) {
  if (typeof data === "string") return data;
  if (data.reply) return data.reply;
  if (data.message) return data.message;
  if (data.response) return data.response;
  if (data.content && Array.isArray(data.content))
    return data.content
      .filter((x) => x.text)
      .map((x) => x.text)
      .join("\n");
  return "Response received.";
}

// ── Send events ──────────────────────────────────────────────────
sendBtn.onclick = () => getBotResponse(input.value);
input.addEventListener("keypress", (e) => {
  if (e.key === "Enter") getBotResponse(input.value);
});

// ── Tab switching ─────────────────────────────────────────────────
document.querySelectorAll(".qtab").forEach((tab) => {
  tab.addEventListener("click", () => {
    document
      .querySelectorAll(".qtab")
      .forEach((t) => t.classList.remove("active"));
    document
      .querySelectorAll(".quick-pane")
      .forEach((p) => p.classList.remove("active"));
    tab.classList.add("active");
    document.getElementById("pane-" + tab.dataset.tab).classList.add("active");
  });
});

// ── Welcome message ──────────────────────────────────────────────
setTimeout(() => {
  addMsg(
    "Welcome to **StayManager AI** 🏨\n\nI'm your intelligent hotel booking assistant. Here's everything I can do for you:\n\n| Action | What I can do |\n|---|---|\n| 🔍 **Search** | Find hotels by location, dates & preferences |\n| ⚖️ **Compare** | Side-by-side hotel comparisons |\n| ✨ **Recommend** | AI-powered personalised suggestions |\n| 🛏️ **Rooms** | Check availability & room details |\n| ✅ **Book** | Reserve rooms instantly |\n| ❌ **Cancel** | Manage & cancel bookings |\n\nUse the quick actions below or just ask me anything!",
    "bot"
  );
}, 600);
