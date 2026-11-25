/* Mental Health Chatbot interactive frontend controller */

document.addEventListener("DOMContentLoaded", () => {
  const chatMessagesEl = document.getElementById("chatMessages");
  const chatForm = document.getElementById("chatForm");
  const messageInput = document.getElementById("messageInput");
  const sendBtn = document.getElementById("sendBtn");
  const typingIndicator = document.getElementById("typingIndicator");
  const sessionListEl = document.getElementById("sessionList");
  const newChatBtn = document.getElementById("newChatBtn");
  const activeSessionTitleEl = document.getElementById("activeSessionTitle");
  const welcomeCardEl = document.getElementById("welcomeCard");
  const engineBadgeEl = document.getElementById("engineBadge");

  const videoModal = document.getElementById("videoModal");
  const videoIframe = document.getElementById("videoIframe");
  const videoModalTitle = document.getElementById("videoModalTitle");
  const modalExternalLink = document.getElementById("modalExternalLink");
  const closeModalBtn = document.getElementById("closeModalBtn");

  const chatSidebar = document.getElementById("chatSidebar");
  const insightsPanel = document.getElementById("insightsPanel");
  const toggleSidebarBtn = document.getElementById("toggleSidebarBtn");
  const toggleInsightsBtn = document.getElementById("toggleInsightsBtn");

  const voiceBtn = document.getElementById("voiceBtn");

  let activeSessionId = null;
  let isSending = false;

  const capitalize = (val) => (val ? val.charAt(0).toUpperCase() + val.slice(1) : "");

  function scrollToBottom() {
    if (chatMessagesEl) {
      chatMessagesEl.scrollTop = chatMessagesEl.scrollHeight;
    }
  }

  function clearMessagesToWelcome() {
    if (!chatMessagesEl) return;
    chatMessagesEl.innerHTML = "";
    if (welcomeCardEl) {
      welcomeCardEl.hidden = false;
      chatMessagesEl.appendChild(welcomeCardEl);
    }
  }

  function createSentimentTag(sentiment, emotion) {
    const tag = document.createElement("span");
    const safeSentiment = ["positive", "negative", "neutral"].includes(sentiment) ? sentiment : "neutral";
    tag.className = `sentiment-tag sentiment-${safeSentiment}`;
    const label = emotion && emotion !== safeSentiment ? `${capitalize(safeSentiment)} · ${capitalize(emotion)}` : capitalize(safeSentiment);
    tag.textContent = label;
    return tag;
  }

  function createVideoCard(video) {
    const card = document.createElement("article");
    card.className = "video-card";

    const thumbWrap = document.createElement("div");
    thumbWrap.className = "video-thumb-wrap";

    const img = document.createElement("img");
    img.src = video.thumbnail_url || `https://img.youtube.com/vi/${video.youtube_id}/hqdefault.jpg`;
    img.alt = video.title;
    img.loading = "lazy";
    thumbWrap.appendChild(img);

    if (video.duration_label) {
      const dur = document.createElement("span");
      dur.className = "video-duration";
      dur.textContent = video.duration_label;
      thumbWrap.appendChild(dur);
    }

    const body = document.createElement("div");
    body.className = "video-card-body";

    body.appendChild(createSentimentTag(video.sentiment, video.emotion_tag));

    const titleEl = document.createElement("h3");
    titleEl.textContent = video.title;
    body.appendChild(titleEl);

    const channelEl = document.createElement("div");
    channelEl.className = "video-channel";
    channelEl.textContent = video.channel || "Curated Mental Health Resource";
    body.appendChild(channelEl);

    if (video.description) {
      const descEl = document.createElement("p");
      descEl.className = "video-desc";
      descEl.textContent = video.description;
      body.appendChild(descEl);
    }

    const actions = document.createElement("div");
    actions.className = "video-card-actions";

    const watchBtn = document.createElement("button");
    watchBtn.type = "button";
    watchBtn.className = "btn btn-primary btn-sm";
    watchBtn.textContent = "Watch Here";
    watchBtn.addEventListener("click", () => openVideoModal(video.youtube_id, video.title, video.url));
    actions.appendChild(watchBtn);

    const extLink = document.createElement("a");
    extLink.href = video.url;
    extLink.target = "_blank";
    extLink.rel = "noopener noreferrer";
    extLink.className = "btn btn-outline btn-sm";
    extLink.textContent = "YouTube ↗";
    actions.appendChild(extLink);

    body.appendChild(actions);
    card.appendChild(thumbWrap);
    card.appendChild(body);
    return card;
  }

  function appendMessage(msg) {
    if (!chatMessagesEl) return;
    if (welcomeCardEl && welcomeCardEl.parentElement === chatMessagesEl) {
      welcomeCardEl.remove();
    }

    const row = document.createElement("div");
    row.className = `message-row ${msg.sender === "user" ? "user" : "bot"}`;

    const bubble = document.createElement("div");
    bubble.className = "message-bubble";
    bubble.textContent = msg.message_text;
    row.appendChild(bubble);

    const meta = document.createElement("div");
    meta.className = "message-meta";

    if (msg.sender === "user" && msg.sentiment) {
      meta.appendChild(createSentimentTag(msg.sentiment, msg.emotion));
      if (typeof msg.sentiment_score === "number") {
        const scoreSpan = document.createElement("span");
        scoreSpan.textContent = `Score: ${msg.sentiment_score >= 0 ? "+" : ""}${msg.sentiment_score.toFixed(2)}`;
        meta.appendChild(scoreSpan);
      }
    } else if (msg.sender === "bot") {
      const roleSpan = document.createElement("span");
      roleSpan.textContent = msg.engine_used === "rasa" ? "Therapist Bot (Rasa NLU)" : "Therapist Bot";
      meta.appendChild(roleSpan);
    }

    if (meta.childNodes.length > 0) {
      row.appendChild(meta);
    }

    if (msg.sender === "bot" && Array.isArray(msg.videos) && msg.videos.length > 0) {
      const grid = document.createElement("div");
      grid.className = "video-cards-grid";
      msg.videos.forEach((video) => grid.appendChild(createVideoCard(video)));
      row.appendChild(grid);
    }

    chatMessagesEl.appendChild(row);
    scrollToBottom();
  }

  function renderSparkline(timeline) {
    const svg = document.getElementById("moodSparkline");
    if (!svg) return;
    svg.innerHTML = "";

    const w = 260;
    const h = 72;
    const padX = 12;
    const padY = 10;

    // Zero baseline
    const midLine = document.createElementNS("http://www.w3.org/2000/svg", "line");
    midLine.setAttribute("x1", "0");
    midLine.setAttribute("x2", String(w));
    midLine.setAttribute("y1", String(h / 2));
    midLine.setAttribute("y2", String(h / 2));
    midLine.setAttribute("stroke", "#dce4dc");
    midLine.setAttribute("stroke-dasharray", "3 3");
    svg.appendChild(midLine);

    if (!timeline || timeline.length === 0) return;

    const coords = timeline.map((pt, idx) => {
      const x = timeline.length === 1
        ? w / 2
        : padX + (idx / (timeline.length - 1)) * (w - padX * 2);
      const clamped = Math.max(-1, Math.min(1, Number(pt.score) || 0));
      const y = h / 2 - clamped * ((h - padY * 2) / 2);
      return { x, y, sentiment: pt.sentiment };
    });

    if (coords.length > 1) {
      const poly = document.createElementNS("http://www.w3.org/2000/svg", "polyline");
      poly.setAttribute("fill", "none");
      poly.setAttribute("stroke", "#2b675c");
      poly.setAttribute("stroke-width", "2.2");
      poly.setAttribute("points", coords.map((c) => `${c.x.toFixed(1)},${c.y.toFixed(1)}`).join(" "));
      svg.appendChild(poly);
    }

    const colorMap = { positive: "#2c8f58", neutral: "#6d8597", negative: "#c54c4c" };
    coords.forEach((c) => {
      const circle = document.createElementNS("http://www.w3.org/2000/svg", "circle");
      circle.setAttribute("cx", c.x.toFixed(1));
      circle.setAttribute("cy", c.y.toFixed(1));
      circle.setAttribute("r", "4");
      circle.setAttribute("fill", colorMap[c.sentiment] || "#2b675c");
      svg.appendChild(circle);
    });
  }

  function updateAnalyticsUI(summary, timeline) {
    if (!summary) return;
    const dominantEl = document.getElementById("dominantSentiment");
    const avgScoreEl = document.getElementById("avgScore");
    const totalLogsEl = document.getElementById("totalLogs");
    const trendBadgeEl = document.getElementById("trendBadge");

    if (dominantEl) dominantEl.textContent = capitalize(summary.dominant_sentiment || "neutral");
    if (avgScoreEl) {
      const score = Number(summary.average_score || 0);
      avgScoreEl.textContent = `${score >= 0 ? "+" : ""}${score.toFixed(2)}`;
    }
    if (totalLogsEl) totalLogsEl.textContent = String(summary.total_messages || 0);

    if (trendBadgeEl) {
      const trend = summary.trend || "initial";
      trendBadgeEl.className = `trend-badge trend-${trend}`;
      trendBadgeEl.textContent = capitalize(trend);
    }

    const setBar = (barId, pctId, pctVal) => {
      const bar = document.getElementById(barId);
      const pct = document.getElementById(pctId);
      const clean = Math.max(0, Math.min(100, Number(pctVal) || 0));
      if (bar) bar.style.width = `${clean}%`;
      if (pct) pct.textContent = `${Math.round(clean)}%`;
    };

    setBar("posBar", "posPct", summary.positive_pct);
    setBar("neuBar", "neuPct", summary.neutral_pct);
    setBar("negBar", "negPct", summary.negative_pct);

    if (Array.isArray(timeline)) {
      renderSparkline(timeline);
    }
  }

  async function refreshAnalytics(sessionId) {
    const query = sessionId ? `?session_id=${encodeURIComponent(sessionId)}` : "";
    try {
      const resp = await fetch(`/api/analytics${query}`);
      if (!resp.ok) return;
      const data = await resp.json();
      updateAnalyticsUI(data.summary, data.timeline);
    } catch (_) {
      // Ignore transient analytics fetch failures
    }
  }

  function highlightActiveSession(sessionId) {
    if (!sessionListEl) return;
    sessionListEl.querySelectorAll(".session-item").forEach((item) => {
      item.classList.toggle("active", Number(item.dataset.sessionId) === Number(sessionId));
    });
  }

  function upsertSessionInSidebar(sessionId, title) {
    if (!sessionListEl) return;
    let item = sessionListEl.querySelector(`.session-item[data-session-id="${sessionId}"]`);
    if (!item) {
      item = document.createElement("li");
      item.className = "session-item";
      item.dataset.sessionId = String(sessionId);

      const selectBtn = document.createElement("button");
      selectBtn.type = "button";
      selectBtn.className = "session-select-btn";
      selectBtn.dataset.sessionId = String(sessionId);

      const titleSpan = document.createElement("span");
      titleSpan.className = "session-title";
      titleSpan.textContent = title;
      selectBtn.appendChild(titleSpan);

      const delBtn = document.createElement("button");
      delBtn.type = "button";
      delBtn.className = "session-delete-btn";
      delBtn.dataset.sessionId = String(sessionId);
      delBtn.title = "Delete conversation";
      delBtn.setAttribute("aria-label", "Delete conversation");
      delBtn.textContent = "×";

      item.appendChild(selectBtn);
      item.appendChild(delBtn);
      sessionListEl.prepend(item);
    } else {
      const titleSpan = item.querySelector(".session-title");
      if (titleSpan && title) titleSpan.textContent = title;
    }
    highlightActiveSession(sessionId);
  }

  async function loadSession(sessionId) {
    try {
      const resp = await fetch(`/api/sessions/${sessionId}/messages`);
      if (!resp.ok) return;
      const data = await resp.json();
      activeSessionId = data.session.id;
      if (activeSessionTitleEl) {
        activeSessionTitleEl.textContent = data.session.title || "Mental Health Check-In";
      }
      highlightActiveSession(activeSessionId);

      chatMessagesEl.innerHTML = "";
      if (!data.messages || data.messages.length === 0) {
        clearMessagesToWelcome();
      } else {
        data.messages.forEach((msg) => appendMessage(msg));
      }

      if (data.analytics) {
        updateAnalyticsUI(data.analytics.summary, data.analytics.timeline);
      }
    } catch (_) {
      // Ignore network hiccup
    }
  }

  async function createNewConversation() {
    try {
      const resp = await fetch("/api/sessions", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ title: "New Check-In" }),
      });
      if (!resp.ok) return;
      const data = await resp.json();
      activeSessionId = data.session.id;
      upsertSessionInSidebar(activeSessionId, data.session.title);
      if (activeSessionTitleEl) activeSessionTitleEl.textContent = data.session.title;
      clearMessagesToWelcome();
      updateAnalyticsUI({
        dominant_sentiment: "neutral",
        average_score: 0,
        total_messages: 0,
        positive_pct: 0,
        neutral_pct: 0,
        negative_pct: 0,
        trend: "initial",
      }, []);
    } catch (_) {
      // Ignore
    }
  }

  async function deleteSession(sessionId) {
    try {
      const resp = await fetch(`/api/sessions/${sessionId}`, { method: "DELETE" });
      if (!resp.ok) return;
      const item = sessionListEl?.querySelector(`.session-item[data-session-id="${sessionId}"]`);
      item?.remove();

      if (Number(activeSessionId) === Number(sessionId)) {
        activeSessionId = null;
        if (activeSessionTitleEl) activeSessionTitleEl.textContent = "Mental Health Check-In";
        clearMessagesToWelcome();
        refreshAnalytics(null);
      }
    } catch (_) {
      // Ignore
    }
  }

  async function sendMessage(rawText) {
    const message = rawText.trim();
    if (!message || isSending) return;

    isSending = true;
    sendBtn.disabled = true;
    if (typingIndicator) typingIndicator.hidden = false;

    const optimisticUser = {
      sender: "user",
      message_text: message,
      sentiment: null,
    };
    appendMessage(optimisticUser);
    const optimisticRow = chatMessagesEl.lastElementChild;

    messageInput.value = "";
    messageInput.style.height = "auto";

    try {
      const resp = await fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          message,
          session_id: activeSessionId,
        }),
      });

      const data = await resp.json();
      if (!resp.ok) {
        if (optimisticRow) optimisticRow.remove();
        appendMessage({
          sender: "bot",
          message_text: data.error || "Sorry, something went wrong. Please try again.",
          engine_used: "local",
        });
        return;
      }

      activeSessionId = data.session_id;
      upsertSessionInSidebar(activeSessionId, data.session_title);
      if (activeSessionTitleEl) activeSessionTitleEl.textContent = data.session_title;

      if (engineBadgeEl) {
        const isRasa = data.engine_used === "rasa";
        engineBadgeEl.className = `status-pill ${isRasa ? "status-online" : "status-fallback"}`;
        engineBadgeEl.textContent = isRasa ? "Rasa NLU Active" : "Local NLU Mode";
      }

      // Replace optimistic user message with analyzed user message (showing sentiment & score)
      if (optimisticRow) optimisticRow.remove();
      appendMessage(data.user_message);
      appendMessage(data.bot_message);

      await refreshAnalytics(activeSessionId);
    } catch (_) {
      appendMessage({
        sender: "bot",
        message_text: "Network error reaching the server. Please check your connection and try again.",
        engine_used: "local",
      });
    } finally {
      isSending = false;
      sendBtn.disabled = false;
      if (typingIndicator) typingIndicator.hidden = true;
      messageInput.focus();
    }
  }

  function openVideoModal(youtubeId, title, externalUrl) {
    if (!videoModal || !videoIframe) return;
    if (videoModalTitle) videoModalTitle.textContent = title || "Recommended Video";
    if (modalExternalLink) modalExternalLink.href = externalUrl || `https://www.youtube.com/watch?v=${youtubeId}`;
    videoIframe.src = `https://www.youtube.com/embed/${youtubeId}?autoplay=1&rel=0`;
    videoModal.hidden = false;
  }

  function closeVideoModal() {
    if (!videoModal || !videoIframe) return;
    videoIframe.src = "";
    videoModal.hidden = true;
  }

  // Event bindings
  if (chatForm) {
    chatForm.addEventListener("submit", (e) => {
      e.preventDefault();
      sendMessage(messageInput.value);
    });
  }

  if (messageInput) {
    messageInput.addEventListener("input", () => {
      messageInput.style.height = "auto";
      messageInput.style.height = `${Math.min(140, messageInput.scrollHeight)}px`;
    });
    messageInput.addEventListener("keydown", (e) => {
      if (e.key === "Enter" && !e.shiftKey) {
        e.preventDefault();
        sendMessage(messageInput.value);
      }
    });
  }

  document.querySelectorAll(".chip-btn").forEach((chip) => {
    chip.addEventListener("click", () => {
      const prompt = chip.getAttribute("data-prompt");
      if (prompt) sendMessage(prompt);
    });
  });

  if (newChatBtn) {
    newChatBtn.addEventListener("click", createNewConversation);
  }

  if (sessionListEl) {
    sessionListEl.addEventListener("click", (e) => {
      const delBtn = e.target.closest(".session-delete-btn");
      if (delBtn) {
        deleteSession(delBtn.dataset.sessionId);
        return;
      }
      const selectBtn = e.target.closest(".session-select-btn");
      if (selectBtn) {
        loadSession(selectBtn.dataset.sessionId);
        chatSidebar?.classList.remove("open");
      }
    });
  }

  // Video library filter tabs & watch buttons
  document.querySelectorAll(".filter-tab").forEach((tab) => {
    tab.addEventListener("click", () => {
      document.querySelectorAll(".filter-tab").forEach((t) => t.classList.remove("active"));
      tab.classList.add("active");
      const filter = tab.getAttribute("data-filter");
      document.querySelectorAll("#videoLibraryList .library-item").forEach((item) => {
        const show = filter === "all" || item.dataset.sentiment === filter;
        item.style.display = show ? "grid" : "none";
      });
    });
  });

  document.querySelectorAll(".watch-video-btn").forEach((btn) => {
    btn.addEventListener("click", () => {
      openVideoModal(btn.dataset.youtubeId, btn.dataset.title, btn.dataset.url);
    });
  });

  if (closeModalBtn) closeModalBtn.addEventListener("click", closeVideoModal);
  if (videoModal) {
    videoModal.addEventListener("click", (e) => {
      if (e.target === videoModal) closeVideoModal();
    });
  }
  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape" && videoModal && !videoModal.hidden) {
      closeVideoModal();
    }
  });

  if (toggleSidebarBtn && chatSidebar) {
    toggleSidebarBtn.addEventListener("click", () => {
      chatSidebar.classList.toggle("open");
    });
  }
  if (toggleInsightsBtn && insightsPanel) {
    toggleInsightsBtn.addEventListener("click", () => {
      insightsPanel.classList.toggle("open");
    });
  }

  // Optional Web Speech API voice dictation
  const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
  if (SpeechRecognition && voiceBtn) {
    voiceBtn.hidden = false;
    const recognition = new SpeechRecognition();
    recognition.lang = "en-US";
    recognition.interimResults = false;

    voiceBtn.addEventListener("click", () => {
      voiceBtn.classList.add("listening");
      recognition.start();
    });
    recognition.addEventListener("result", (event) => {
      const transcript = event.results?.[0]?.[0]?.transcript || "";
      if (transcript) {
        messageInput.value = `${messageInput.value} ${transcript}`.trim();
        messageInput.focus();
      }
    });
    recognition.addEventListener("end", () => {
      voiceBtn.classList.remove("listening");
    });
    recognition.addEventListener("error", () => {
      voiceBtn.classList.remove("listening");
    });
  }

  // Auto-load most recent session if available, else show user-wide analytics
  const firstSessionBtn = sessionListEl?.querySelector(".session-select-btn");
  if (firstSessionBtn) {
    loadSession(firstSessionBtn.dataset.sessionId);
  } else {
    refreshAnalytics(null);
  }
});
