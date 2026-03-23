import { useState, useEffect, useRef, useCallback } from "react";

// ── Marked CDN loaded via useEffect ──────────────────────────────
// We'll use a simple markdown parser inline to avoid CDN dependencies

function parseMarkdown(text) {
  // Simple markdown parser
  let html = text
    // Escape HTML first
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    // Tables
    .replace(/^\|(.+)\|\s*$/gm, (match) => {
      const cells = match.split("|").filter((c) => c.trim() !== "");
      return "<tr>" + cells.map((c) => `<td>${c.trim()}</td>`).join("") + "</tr>";
    })
    // Headers
    .replace(/^#### (.+)$/gm, "<h4>$1</h4>")
    .replace(/^### (.+)$/gm, "<h3>$1</h3>")
    .replace(/^## (.+)$/gm, "<h2>$1</h2>")
    .replace(/^# (.+)$/gm, "<h1>$1</h1>")
    // Bold
    .replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>")
    // Italic
    .replace(/\*(.+?)\*/g, "<em>$1</em>")
    // Code
    .replace(/`(.+?)`/g, "<code>$1</code>")
    // HR
    .replace(/^---$/gm, "<hr/>")
    // Lists
    .replace(/^\- (.+)$/gm, "<li>$1</li>")
    // Blockquote
    .replace(/^> (.+)$/gm, "<blockquote>$1</blockquote>")
    // Line breaks
    .replace(/\n/g, "<br/>");

  // Wrap consecutive <tr> in <table>
  html = html.replace(/(<tr>.*?<\/tr>(<br\/>)?)+/g, (match) => {
    const rows = match.replace(/<br\/>/g, "").split("</tr>").filter((r) => r.includes("<tr>"));
    const [header, ...rest] = rows;
    const thRow = header.replace(/<td>/g, "<th>").replace(/<\/td>/g, "</th>");
    return `<table><thead>${thRow}</tr></thead><tbody>${rest.map((r) => r + "</tr>").join("")}</tbody></table>`;
  });

  // Wrap <li> in <ul>
  html = html.replace(/(<li>.*?<\/li>(<br\/>)?)+/g, (match) => {
    return `<ul>${match.replace(/<br\/>/g, "")}</ul>`;
  });

  return html;
}

// ── Icons ─────────────────────────────────────────────────────────
const HomeIcon = () => (
  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/>
    <polyline points="9 22 9 12 15 12 15 22"/>
  </svg>
);
const ChatIcon = () => (
  <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
  </svg>
);
const RefreshIcon = () => (
  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <polyline points="1 4 1 10 7 10"/><path d="M3.51 15a9 9 0 1 0 .49-3.87"/>
  </svg>
);
const ExpandIcon = () => (
  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <polyline points="15 3 21 3 21 9"/><polyline points="9 21 3 21 3 15"/>
    <line x1="21" y1="3" x2="14" y2="10"/><line x1="3" y1="21" x2="10" y2="14"/>
  </svg>
);
const ShrinkIcon = () => (
  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <polyline points="4 14 10 14 10 20"/><polyline points="20 10 14 10 14 4"/>
    <line x1="10" y1="14" x2="3" y2="21"/><line x1="21" y1="3" x2="14" y2="10"/>
  </svg>
);
const CloseIcon = () => (
  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/>
  </svg>
);
const SendIcon = () => (
  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
    <line x1="22" y1="2" x2="11" y2="13"/><polygon points="22 2 15 22 11 13 2 9 22 2"/>
  </svg>
);
const BotAvatarIcon = () => (
  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#c9a86c" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/>
    <polyline points="9 22 9 12 15 12 15 22"/>
  </svg>
);
const UserAvatarIcon = () => (
  <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="#a78bfa" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/>
  </svg>
);

// ── Helpers ───────────────────────────────────────────────────────
function getNow() {
  const d = new Date();
  let h = d.getHours(), m = String(d.getMinutes()).padStart(2, "0");
  const ap = h >= 12 ? "PM" : "AM";
  h = h % 12 || 12;
  return `${h}:${m} ${ap}`;
}

function generateSessionId() {
  return "stay-" + Math.random().toString(36).substring(2, 9);
}

function extractReply(data) {
  if (typeof data === "string") return data;
  if (data.reply) return data.reply;
  if (data.message) return data.message;
  if (data.response) return data.response;
  if (data.content && Array.isArray(data.content))
    return data.content.filter((x) => x.text).map((x) => x.text).join("\n");
  return "Response received.";
}

const WELCOME_MSG = `Welcome to **StayManager AI** 🏨\n\nI'm your intelligent hotel booking assistant. Here's everything I can do for you:\n\n| Action | What I can do |\n|---|---|\n| 🔍 **Search** | Find hotels by location, dates & preferences |\n| ⚖️ **Compare** | Side-by-side hotel comparisons |\n| ✨ **Recommend** | AI-powered personalised suggestions |\n| 🛏️ **Rooms** | Check availability & room details |\n| ✅ **Book** | Reserve rooms instantly |\n| ❌ **Cancel** | Manage & cancel bookings |\n\nUse the quick actions below or just ask me anything!`;

const TABS = ["discover", "rooms", "bookings"];
const QUICK_ACTIONS = {
  discover: [
    { icon: "🏨", label: "Find Hotels", text: "Search for hotels in New York" },
    { icon: "⚖️", label: "Compare Hotels", text: "Compare top hotels for me" },
    { icon: "✨", label: "AI Picks", text: "Give me AI hotel recommendations" },
    { icon: "ℹ️", label: "Hotel Info", text: "Show me hotel details" },
  ],
  rooms: [
    { icon: "🗓️", label: "Check Availability", text: "Check room availability" },
    { icon: "🔑", label: "Room Details", text: "Show me room details and pricing" },
    { icon: "🏷️", label: "Room Types", text: "What room types are available?" },
  ],
  bookings: [
    { icon: "✅", label: "Book a Room", text: "I want to book a room" },
    { icon: "❌", label: "Cancel Booking", text: "Cancel my booking" },
    { icon: "📄", label: "My Bookings", text: "Show my booking details" },
  ],
};

// ── Styles ────────────────────────────────────────────────────────
const styles = `
  @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@400;600&family=DM+Sans:wght@300;400;500;600&display=swap');

  *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

  :root {
    --ink: #0a0a0f;
    --ink-soft: #1c1c26;
    --gold: #c9a86c;
    --gold-dim: #a88a50;
    --gold-glow: rgba(201,168,108,0.18);
    --cream: #f5f0e8;
    --cream-dim: #ede8df;
    --mist: rgba(245,240,232,0.06);
    --border: rgba(201,168,108,0.2);
    --border-hi: rgba(201,168,108,0.5);
    --text-main: #f5f0e8;
    --text-soft: rgba(245,240,232,0.55);
    --text-xsoft: #c4bfb5;
    --radius-card: 20px;
    --radius-pill: 50px;
    --shadow-float: 0 32px 80px -12px rgba(0,0,0,0.7), 0 0 0 1px var(--border);
  }

  body { font-family: "DM Sans", sans-serif; background: #0e0e12; min-height: 100vh; }

  .sm-demo-bg {
    position: fixed; inset: 0; z-index: 0;
    background: radial-gradient(ellipse 60% 60% at 20% 80%, rgba(201,168,108,0.07) 0%, transparent 60%),
                radial-gradient(ellipse 40% 40% at 80% 20%, rgba(60,40,100,0.12) 0%, transparent 60%), #0a0a0f;
  }

  /* Toggle */
  .sm-toggle {
    position: fixed; bottom: 28px; right: 28px;
    width: 60px; height: 60px; border-radius: 50%;
    border: 1px solid var(--border-hi);
    background: linear-gradient(145deg, #1a1720, #0f0d14);
    color: var(--gold); cursor: pointer; z-index: 1001;
    box-shadow: 0 8px 30px rgba(0,0,0,0.5), 0 0 0 1px var(--border), inset 0 1px 0 rgba(255,255,255,0.06);
    transition: transform 0.3s cubic-bezier(0.34,1.56,0.64,1), box-shadow 0.3s;
    display: flex; align-items: center; justify-content: center;
  }
  .sm-toggle:hover {
    transform: scale(1.08) translateY(-2px);
    box-shadow: 0 12px 40px rgba(0,0,0,0.6), 0 0 20px var(--gold-glow), 0 0 0 1px var(--border-hi);
  }
  .sm-toggle svg { filter: drop-shadow(0 0 8px var(--gold-glow)); }
  .sm-toggle::before {
    content: ""; position: absolute; inset: -6px; border-radius: 50%;
    border: 1px solid var(--gold); opacity: 0;
    animation: pulse-ring 3s ease-out infinite;
  }
  @keyframes pulse-ring {
    0% { opacity: 0.4; transform: scale(0.9); }
    80% { opacity: 0; transform: scale(1.3); }
    100% { opacity: 0; }
  }

  /* Container */
  .sm-container {
    position: fixed; top: 0; bottom: 0; right: 0;
    width: calc(100vw / 3); height: 100vh;
    background: linear-gradient(170deg, #151318 0%, #0f0d14 100%);
    border-radius: var(--radius-card) 0 0 var(--radius-card);
    border: 1px solid var(--border); border-right: none;
    box-shadow: var(--shadow-float);
    display: flex; flex-direction: column; overflow: hidden;
    z-index: 1000; opacity: 0;
    transform: translateX(40px) scale(0.98);
    pointer-events: none;
    transition: opacity 0.35s ease, transform 0.4s cubic-bezier(0.175,0.885,0.32,1.15),
                width 0.45s cubic-bezier(0.4,0,0.2,1), border-radius 0.45s cubic-bezier(0.4,0,0.2,1);
  }
  .sm-container.active { opacity: 1; transform: translateX(0) scale(1); pointer-events: all; }
  .sm-container.fullscreen { width: 100vw; border-radius: 0; border: none; box-shadow: none; }

  /* Header */
  .sm-header {
    padding: 0 20px; height: 70px;
    display: flex; align-items: center; justify-content: space-between;
    background: linear-gradient(90deg, rgba(201,168,108,0.06) 0%, transparent 100%);
    border-bottom: 1px solid var(--border); position: relative; flex-shrink: 0;
  }
  .sm-header::before {
    content: ""; position: absolute; top: 0; left: 0; right: 0; height: 1px;
    background: linear-gradient(90deg, transparent, var(--gold), transparent); opacity: 0.5;
  }
  .sm-header-left { display: flex; align-items: center; gap: 14px; }
  .sm-avatar {
    width: 40px; height: 40px; border-radius: 12px;
    background: linear-gradient(135deg, #2a2118, #1a150e);
    border: 1px solid var(--border-hi);
    display: flex; align-items: center; justify-content: center;
    position: relative;
    box-shadow: 0 4px 12px rgba(0,0,0,0.3), inset 0 1px 0 rgba(201,168,108,0.1);
  }
  .sm-avatar svg { color: var(--gold); }
  .sm-online-dot {
    position: absolute; bottom: -3px; right: -3px;
    width: 11px; height: 11px; border-radius: 50%;
    background: #22c55e; border: 2px solid #151318;
    box-shadow: 0 0 6px rgba(34,197,94,0.4);
  }
  .sm-header-info h3 {
    font-family: "Playfair Display", serif; font-size: 15px;
    font-weight: 600; letter-spacing: 0.01em; color: var(--text-main);
  }
  .sm-header-info p {
    font-size: 11px; color: var(--gold); letter-spacing: 0.06em;
    text-transform: uppercase; margin-top: 2px;
  }
  .sm-header-actions { display: flex; align-items: center; gap: 8px; }
  .sm-icon-btn {
    width: 34px; height: 34px; border-radius: 10px;
    border: 1px solid var(--border); background: var(--mist);
    color: var(--text-soft);
    display: flex; align-items: center; justify-content: center;
    cursor: pointer; transition: all 0.2s;
  }
  .sm-icon-btn:hover { border-color: var(--border-hi); color: var(--gold); background: var(--gold-glow); }
  .sm-close-btn { transition: all 0.2s; }
  .sm-close-btn:hover { transform: rotate(90deg); }

  /* Chat window */
  .sm-chat-window {
    flex: 1; padding: 20px 18px; overflow-y: auto;
    display: flex; flex-direction: column; gap: 14px;
  }
  .sm-chat-window::-webkit-scrollbar { width: 4px; }
  .sm-chat-window::-webkit-scrollbar-track { background: transparent; }
  .sm-chat-window::-webkit-scrollbar-thumb { background: rgba(201,168,108,0.2); border-radius: 4px; }
  .sm-chat-window::-webkit-scrollbar-thumb:hover { background: rgba(201,168,108,0.35); }

  /* Date divider */
  .sm-date-divider {
    display: flex; align-items: center; gap: 12px;
    color: var(--text-xsoft); font-size: 11px; letter-spacing: 0.08em;
    text-transform: uppercase; margin: 4px 0;
  }
  .sm-date-divider::before, .sm-date-divider::after { content: ""; flex: 1; height: 1px; }
  .sm-date-divider::before { background: linear-gradient(90deg, transparent, var(--border)); }
  .sm-date-divider::after { background: linear-gradient(90deg, var(--border), transparent); }

  /* Messages */
  @keyframes msgIn {
    from { opacity: 0; transform: translateY(12px) scale(0.97); }
    to { opacity: 1; transform: translateY(0) scale(1); }
  }
  .sm-msg { display: flex; gap: 10px; align-items: flex-end; animation: msgIn 0.35s cubic-bezier(0.34,1.3,0.64,1) forwards; }
  .sm-msg.user { flex-direction: row-reverse; }
  .sm-msg-avatar {
    width: 30px; height: 30px; border-radius: 9px; flex-shrink: 0;
    display: flex; align-items: center; justify-content: center; font-size: 11px;
  }
  .sm-msg-avatar.bot { background: linear-gradient(135deg,#2a2118,#1a150e); border: 1px solid var(--border-hi); color: var(--gold); }
  .sm-msg-avatar.user { background: linear-gradient(135deg,#1e1b2e,#141220); border: 1px solid rgba(139,92,246,0.3); color: #a78bfa; }
  .sm-msg-body { max-width: 82%; }
  .sm-msg-bubble { padding: 12px 15px; font-size: 13.5px; line-height: 1.65; word-wrap: break-word; }
  .sm-msg-bubble.bot {
    background: linear-gradient(135deg, rgba(255,255,255,0.05), rgba(255,255,255,0.02));
    border: 1px solid var(--border); border-radius: 16px 16px 16px 4px;
    color: var(--cream); box-shadow: 0 4px 20px rgba(0,0,0,0.2); backdrop-filter: blur(10px);
  }
  .sm-msg-bubble.user {
    background: linear-gradient(135deg, rgba(201,168,108,0.15), rgba(201,168,108,0.08));
    border: 1px solid rgba(201,168,108,0.3); border-radius: 16px 16px 4px 16px;
    color: var(--cream); box-shadow: 0 4px 20px rgba(0,0,0,0.2);
  }
  .sm-msg-time { font-size: 10.5px; color: var(--text-soft); margin-top: 5px; padding: 0 3px; letter-spacing: 0.02em; }
  .sm-msg.user .sm-msg-time { text-align: right; }

  /* Markdown styles inside bubble */
  .sm-msg-bubble h1, .sm-msg-bubble h2, .sm-msg-bubble h3, .sm-msg-bubble h4 {
    font-family: "Playfair Display", serif; color: var(--gold);
    margin: 14px 0 8px 0; font-size: 14px; font-weight: 600;
  }
  .sm-msg-bubble h3:first-child, .sm-msg-bubble h4:first-child { margin-top: 0; }
  .sm-msg-bubble strong { color: var(--gold); font-weight: 600; }
  .sm-msg-bubble em { color: var(--text-xsoft); font-style: italic; }
  .sm-msg-bubble p { margin-bottom: 8px; }
  .sm-msg-bubble p:last-child { margin-bottom: 0; }
  .sm-msg-bubble ul { padding-left: 0; margin-bottom: 10px; list-style: none; }
  .sm-msg-bubble ul li { padding-left: 16px; position: relative; margin-bottom: 5px; color: var(--cream-dim); }
  .sm-msg-bubble ul li::before { content: "▸"; position: absolute; left: 0; color: var(--gold); font-size: 10px; top: 2px; }
  .sm-msg-bubble ol { padding-left: 18px; margin-bottom: 10px; }
  .sm-msg-bubble ol li { margin-bottom: 5px; color: var(--cream-dim); }
  .sm-msg-bubble ol li::marker { color: var(--gold); }
  .sm-msg-bubble hr { border: none; border-top: 1px solid var(--border); margin: 12px 0; }
  .sm-msg-bubble code { background: rgba(201,168,108,0.1); color: var(--gold); padding: 1px 6px; border-radius: 4px; font-size: 12px; font-family: monospace; }
  .sm-msg-bubble blockquote { border-left: 2px solid var(--gold); padding-left: 12px; margin: 8px 0; color: var(--text-xsoft); font-style: italic; }
  .sm-msg-bubble table { width: 100%; border-collapse: collapse; margin: 12px 0; font-size: 12.5px; border-radius: 10px; overflow: hidden; border: 1px solid var(--border); }
  .sm-msg-bubble th { background: rgba(201,168,108,0.1); color: var(--gold); padding: 9px 12px; text-align: left; font-weight: 600; font-size: 11px; text-transform: uppercase; letter-spacing: 0.05em; border-bottom: 1px solid var(--border); }
  .sm-msg-bubble td { padding: 9px 12px; color: var(--cream-dim); border-bottom: 1px solid rgba(201,168,108,0.08); }
  .sm-msg-bubble tr:last-child td { border-bottom: none; }
  .sm-msg-bubble tr:hover td { background: rgba(201,168,108,0.04); }

  /* Typing */
  .sm-typing-wrap { padding: 0 18px 12px; display: flex; gap: 10px; align-items: flex-end; }
  .sm-typing-avatar {
    width: 30px; height: 30px; border-radius: 9px; flex-shrink: 0;
    background: linear-gradient(135deg,#2a2118,#1a150e);
    border: 1px solid var(--border-hi);
    display: flex; align-items: center; justify-content: center;
  }
  .sm-typing-dots {
    display: inline-flex; gap: 5px; padding: 13px 16px;
    background: linear-gradient(135deg, rgba(255,255,255,0.05), rgba(255,255,255,0.02));
    border: 1px solid var(--border); border-radius: 16px 16px 16px 4px;
  }
  .sm-typing-dots span {
    width: 5px; height: 5px; border-radius: 50%; background: var(--gold); opacity: 0.5;
    animation: typeBounce 1.5s infinite ease-in-out both;
  }
  .sm-typing-dots span:nth-child(1) { animation-delay: -0.32s; }
  .sm-typing-dots span:nth-child(2) { animation-delay: -0.16s; }
  @keyframes typeBounce {
    0%, 80%, 100% { transform: translateY(0); opacity: 0.3; }
    40% { transform: translateY(-5px); opacity: 1; }
  }

  /* Quick panel */
  .sm-quick-panel { flex-shrink: 0; border-top: 1px solid var(--border); background: rgba(255,255,255,0.015); }
  .sm-quick-tabs { display: flex; border-bottom: 1px solid var(--border); }
  .sm-qtab {
    flex: 1; padding: 9px 4px; font-size: 11px; font-weight: 500;
    font-family: "DM Sans", sans-serif; letter-spacing: 0.04em;
    text-transform: uppercase; color: var(--text-soft); background: none;
    border: none; cursor: pointer; border-bottom: 2px solid transparent;
    margin-bottom: -1px; transition: color 0.2s, border-color 0.2s;
  }
  .sm-qtab:hover { color: var(--text-xsoft); }
  .sm-qtab.active { color: var(--gold); border-bottom-color: var(--gold); }
  .sm-quick-pane { display: flex; padding: 10px 14px 12px; flex-wrap: wrap; gap: 7px; }
  .sm-chip {
    display: flex; align-items: center; gap: 6px; padding: 7px 13px;
    border-radius: var(--radius-pill); border: 1px solid var(--border);
    background: var(--mist); font-size: 12px; font-weight: 500;
    color: var(--text-xsoft); cursor: pointer; white-space: nowrap;
    transition: all 0.22s cubic-bezier(0.34,1.2,0.64,1);
    font-family: "DM Sans", sans-serif; letter-spacing: 0.01em;
  }
  .sm-chip:hover {
    border-color: var(--border-hi); color: var(--gold); background: var(--gold-glow);
    transform: translateY(-2px); box-shadow: 0 6px 20px rgba(0,0,0,0.25);
  }
  .sm-chip-icon { font-size: 13px; }

  /* Input */
  .sm-input-wrap { padding: 14px 16px; border-top: 1px solid var(--border); background: rgba(255,255,255,0.015); flex-shrink: 0; }
  .sm-input-row {
    display: flex; align-items: center; gap: 10px;
    background: rgba(255,255,255,0.04); border: 1px solid var(--border);
    border-radius: var(--radius-pill); padding: 6px 6px 6px 16px;
    transition: border-color 0.2s, box-shadow 0.2s;
  }
  .sm-input-row:focus-within { border-color: var(--border-hi); box-shadow: 0 0 0 3px var(--gold-glow); }
  .sm-input {
    flex: 1; background: transparent; border: none; outline: none;
    font-size: 13.5px; font-family: "DM Sans", sans-serif;
    color: var(--text-main); caret-color: var(--gold);
  }
  .sm-input::placeholder { color: var(--text-soft); }
  .sm-send-btn {
    width: 38px; height: 38px; border-radius: 50%; border: none; flex-shrink: 0;
    background: linear-gradient(135deg, var(--gold), var(--gold-dim));
    color: var(--ink); cursor: pointer;
    display: flex; align-items: center; justify-content: center;
    transition: all 0.2s cubic-bezier(0.34,1.4,0.64,1);
    box-shadow: 0 4px 12px rgba(201,168,108,0.25);
  }
  .sm-send-btn:hover { transform: scale(1.1) translateY(-1px); box-shadow: 0 6px 20px rgba(201,168,108,0.35); }
  .sm-send-btn:active { transform: scale(0.95); }

  @media (max-width: 768px) {
    .sm-container:not(.fullscreen) { width: 85vw; border-radius: 16px 0 0 16px; }
  }
`;

// ── Message Component ─────────────────────────────────────────────
function Message({ text, sender, time }) {
  const isBot = sender === "bot";
  return (
    <div className={`sm-msg ${sender}`}>
      <div className={`sm-msg-avatar ${sender}`}>
        {isBot ? <BotAvatarIcon /> : <UserAvatarIcon />}
      </div>
      <div className="sm-msg-body">
        <div
          className={`sm-msg-bubble ${sender}`}
          {...(isBot
            ? { dangerouslySetInnerHTML: { __html: parseMarkdown(text) } }
            : { children: text }
          )}
        />
        <div className="sm-msg-time">{time}</div>
      </div>
    </div>
  );
}

// ── Typing Indicator ──────────────────────────────────────────────
function TypingIndicator() {
  return (
    <div className="sm-typing-wrap">
      <div className="sm-typing-avatar">
        <BotAvatarIcon />
      </div>
      <div className="sm-typing-dots">
        <span /><span /><span />
      </div>
    </div>
  );
}

// ── Main Component ────────────────────────────────────────────────
export default function StayManagerChat() {
  const [isOpen, setIsOpen] = useState(false);
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [messages, setMessages] = useState([]);
  const [inputVal, setInputVal] = useState("");
  const [isTyping, setIsTyping] = useState(false);
  const [activeTab, setActiveTab] = useState("discover");
  const [sessionId] = useState(generateSessionId);
  const chatWindowRef = useRef(null);
  const inputRef = useRef(null);

  // Inject styles once
  useEffect(() => {
    const styleEl = document.createElement("style");
    styleEl.textContent = styles;
    document.head.appendChild(styleEl);
    return () => document.head.removeChild(styleEl);
  }, []);

  // Welcome message
  useEffect(() => {
    const t = setTimeout(() => {
      setMessages([{ id: Date.now(), text: WELCOME_MSG, sender: "bot", time: getNow() }]);
    }, 600);
    return () => clearTimeout(t);
  }, []);

  // Scroll to bottom
  useEffect(() => {
    if (chatWindowRef.current) {
      chatWindowRef.current.scrollTo({ top: chatWindowRef.current.scrollHeight, behavior: "smooth" });
    }
  }, [messages, isTyping]);

  // Escape key exits fullscreen
  useEffect(() => {
    const handler = (e) => {
      if (e.key === "Escape" && isFullscreen) setIsFullscreen(false);
    };
    document.addEventListener("keydown", handler);
    return () => document.removeEventListener("keydown", handler);
  }, [isFullscreen]);

  const addMessage = useCallback((text, sender) => {
    setMessages((prev) => [...prev, { id: Date.now() + Math.random(), text, sender, time: getNow() }]);
  }, []);

  const sendMessage = useCallback(async (text) => {
    if (!text.trim()) return;
    addMessage(text, "user");
    setInputVal("");
    setIsTyping(true);

    try {
      const res = await fetch("http://127.0.0.1:8000/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ session_id: sessionId, message: text }),
      });

      if (!res.ok) {
        const errText = await res.text();
        setIsTyping(false);
        addMessage(`**Error:** Server returned status ${res.status}\n\n${errText}`, "bot");
        return;
      }

      const data = await res.json();
      setIsTyping(false);
      addMessage(extractReply(data), "bot");
    } catch (err) {
      setIsTyping(false);
      addMessage("**Connection Error**\n\nUnable to reach the backend. Please check that the server is running.", "bot");
    }
  }, [sessionId, addMessage]);

  const handleClear = () => {
    setMessages([]);
    setTimeout(() => addMessage("Chat cleared. How can I assist you?", "bot"), 300);
  };

  const handleOpen = () => {
    setIsOpen(true);
    setTimeout(() => inputRef.current?.focus(), 400);
  };

  const handleClose = () => {
    setIsOpen(false);
    setIsFullscreen(false);
  };

  const containerClass = [
    "sm-container",
    isOpen ? "active" : "",
    isFullscreen ? "fullscreen" : "",
  ].filter(Boolean).join(" ");

  return (
    <>
      <div className="sm-demo-bg" />

      {/* Toggle */}
      <button className="sm-toggle" onClick={handleOpen} title="Open StayManager AI">
        <ChatIcon />
      </button>

      {/* Widget */}
      <div className={containerClass}>
        {/* Header */}
        <div className="sm-header">
          <div className="sm-header-left">
            <div className="sm-avatar">
              <HomeIcon />
              <div className="sm-online-dot" />
            </div>
            <div className="sm-header-info">
              <h3>StayManager AI</h3>
              <p>Property &amp; Booking Assistant</p>
            </div>
          </div>
          <div className="sm-header-actions">
            <button className="sm-icon-btn" title="Clear chat" onClick={handleClear}>
              <RefreshIcon />
            </button>
            <button
              className="sm-icon-btn"
              title={isFullscreen ? "Exit fullscreen" : "Expand to fullscreen"}
              onClick={() => setIsFullscreen((f) => !f)}
            >
              {isFullscreen ? <ShrinkIcon /> : <ExpandIcon />}
            </button>
            <button className="sm-icon-btn sm-close-btn" title="Close" onClick={handleClose}>
              <CloseIcon />
            </button>
          </div>
        </div>

        {/* Messages */}
        <div className="sm-chat-window" ref={chatWindowRef}>
          <div className="sm-date-divider">Today</div>
          {messages.map((msg) => (
            <Message key={msg.id} text={msg.text} sender={msg.sender} time={msg.time} />
          ))}
          {isTyping && <TypingIndicator />}
        </div>

        {/* Quick Actions */}
        <div className="sm-quick-panel">
          <div className="sm-quick-tabs">
            {TABS.map((tab) => (
              <button
                key={tab}
                className={`sm-qtab ${activeTab === tab ? "active" : ""}`}
                onClick={() => setActiveTab(tab)}
              >
                {tab === "discover" && "🔍 Discover"}
                {tab === "rooms" && "🛏️ Rooms"}
                {tab === "bookings" && "📋 Bookings"}
              </button>
            ))}
          </div>
          <div className="sm-quick-pane">
            {QUICK_ACTIONS[activeTab].map((action) => (
              <button
                key={action.text}
                className="sm-chip"
                onClick={() => sendMessage(action.text)}
              >
                <span className="sm-chip-icon">{action.icon}</span>
                {action.label}
              </button>
            ))}
          </div>
        </div>

        {/* Input */}
        <div className="sm-input-wrap">
          <div className="sm-input-row">
            <input
              ref={inputRef}
              className="sm-input"
              placeholder="Search hotels, check availability, book rooms…"
              autoComplete="off"
              value={inputVal}
              onChange={(e) => setInputVal(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && sendMessage(inputVal)}
            />
            <button className="sm-send-btn" title="Send" onClick={() => sendMessage(inputVal)}>
              <SendIcon />
            </button>
          </div>
        </div>
      </div>
    </>
  );
}