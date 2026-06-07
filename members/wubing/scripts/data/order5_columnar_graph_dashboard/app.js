const state = {
  summary: null,
  rowMap: null,
  rowMapLayout: null,
  rowNetworkLayout: null,
  targetMap: null,
  targetMapLayout: null,
  targetNetworkLayout: null,
};

const layerColors = {
  unknown: "#e4e8ea",
  true: "#2f7d62",
  false: "#b6493a",
  approx_true: "#927235",
  approx_false: "#927235",
  conflict: "#7c4d9e",
  approx_both: "#65533a",
};

const rowMapCodes = {
  0: { label: "unknown", color: layerColors.unknown },
  1: { label: "true", color: layerColors.true },
  2: { label: "false", color: layerColors.false },
  3: { label: "conflict", color: layerColors.conflict },
  4: { label: "approx_true", color: layerColors.approx_true },
  5: { label: "approx_false", color: layerColors.approx_false },
  6: { label: "approx_both", color: layerColors.approx_both },
};

const layerNotes = {
  true: "exact proof-backed implication",
  false: "exact countermodel-backed non-implication",
  approx_true: "candidate true evidence; not exact",
  approx_false: "candidate false evidence; not exact",
  conflict: "both exact true and exact false are set",
};

const $ = (id) => document.getElementById(id);

async function fetchJson(path, params = {}) {
  const url = new URL(path, window.location.origin);
  for (const [key, value] of Object.entries(params)) {
    if (value !== undefined && value !== null && value !== "") {
      url.searchParams.set(key, value);
    }
  }
  const response = await fetch(url);
  const payload = await response.json();
  if (!response.ok) {
    throw new Error(payload.message || payload.error || `HTTP ${response.status}`);
  }
  return payload;
}

function formatInt(value) {
  if (value === undefined || value === null) return "n/a";
  return Number(value).toLocaleString("en-US");
}

function formatBytes(value) {
  if (value === undefined || value === null) return "n/a";
  const units = ["B", "KiB", "MiB", "GiB", "TiB"];
  let size = Number(value);
  let unit = 0;
  while (size >= 1024 && unit < units.length - 1) {
    size /= 1024;
    unit += 1;
  }
  return `${size.toFixed(unit === 0 ? 0 : 1)} ${units[unit]}`;
}

function formatTime(unixSeconds) {
  if (!unixSeconds) return "n/a";
  return new Date(unixSeconds * 1000).toLocaleString();
}

function shortText(value, max = 86) {
  const text = String(value ?? "");
  return text.length <= max ? text : `${text.slice(0, max - 1)}...`;
}

function showToast(message) {
  const toast = $("toast");
  toast.textContent = message;
  toast.hidden = false;
  window.clearTimeout(showToast.timer);
  showToast.timer = window.setTimeout(() => {
    toast.hidden = true;
  }, 5200);
}

async function refreshSummary({ countBits = false } = {}) {
  setBusy(true);
  try {
    const summary = await fetchJson("/api/summary", {
      count_bits: countBits ? "1" : "",
      evidence_limit: 18,
    });
    state.summary = summary;
    renderSummary(summary);
  } catch (error) {
    showToast(error.message);
  } finally {
    setBusy(false);
  }
}

function setBusy(isBusy) {
  $("countBitsButton").disabled = isBusy;
  $("countBitsButton").textContent = isBusy ? "Refreshing..." : "Refresh solved/unresolved";
}

function renderSummary(summary) {
  $("storePath").textContent = `${summary.store_dir} | ${formatTime(summary.generated_at_unix)}`;
  const exactCounts = summary.exact_counts;
  const countDetail = exactCounts?.counted_at_unix
    ? `counted ${formatTime(exactCounts.counted_at_unix)}`
    : "not counted yet";
  $("metrics").innerHTML = [
    metric("Laws", formatInt(summary.law_count)),
    metric("Pairs", formatInt(summary.pair_count)),
    metric("Exact solved", exactCounts ? formatInt(exactCounts.exact_known_count) : "Refresh", countDetail),
    metric("Exact unresolved", exactCounts ? formatInt(exactCounts.exact_unknown_count) : "Refresh", countDetail),
  ].join("");
  renderLayers(summary.layers);
  renderLayerNotes();
  renderEvidence(summary.evidence);
  renderRowMapLegend();
}

function metric(label, value, detail = "") {
  return `<div class="metric"><div class="label">${label}</div><div class="value">${value}</div>${detail ? `<div class="metric-detail">${detail}</div>` : ""}</div>`;
}

function renderLayers(layers) {
  $("layerStrip").innerHTML = layers
    .map((layer) => {
      const counted = "set_bits" in layer;
      const width = counted ? Math.max(layer.density * 100, layer.set_bits > 0 ? 1 : 0) : 0;
      const stat = counted
        ? `${formatInt(layer.set_bits)} set | ${(layer.density * 100).toFixed(4)}%`
        : `${formatBytes(layer.file.bytes)} | mtime ${formatTime(layer.file.modified_at_unix)}`;
      return `
        <div class="layer-card ${layer.name}" title="${layerNotes[layer.name] || ""}">
          <div class="layer-top">
            <div class="layer-name">${layer.name}</div>
            <span class="dot"></span>
          </div>
          <div class="layer-stat">${stat}</div>
          <div class="bar"><div class="bar-fill" style="width:${width}%;background:${layerColors[layer.name] || "#286da8"}"></div></div>
        </div>
      `;
    })
    .join("");
}

function renderLayerNotes() {
  $("layerNotes").innerHTML = [
    "Exact unresolved = pairs not in true ∪ false.",
    "approx_true / approx_false are candidate layers; they do not close exact claims.",
  ]
    .map((note) => `<span class="layer-note">${note}</span>`)
    .join("");
}

function renderEvidence(evidence) {
  $("evidenceMeta").textContent = `${formatBytes(evidence.batch_log.bytes)} | ${formatInt(evidence.batch_log_line_count)} rows`;
  const rows = [...evidence.last_batches].reverse();
  $("evidenceRows").innerHTML = rows
    .map((row) => `
      <tr>
        <td class="num">${formatTime(row.created_at_unix)}</td>
        <td>${row.layer || ""}</td>
        <td class="num">${formatInt(row.read_count)}</td>
        <td class="num">${formatInt(row.newly_set_count)}</td>
        <td class="num">${formatInt(row.already_set_count)}</td>
        <td class="num">${formatInt(row.conflict_count)}</td>
        <td class="source-cell" title="${String(row.source_id || "")}">${shortText(row.source_id || row.source_path || row.raw || "")}</td>
      </tr>
    `)
    .join("");
}

async function queryRowMap() {
  const equationId = $("mapEquation").value.trim();
  $("rowMapButton").disabled = true;
  $("rowMapMeta").textContent = "loading";
  try {
    const [rowMap, targetMap] = await Promise.all([
      fetchJson("/api/row-map", { source_id: equationId }),
      fetchJson("/api/target-map", { target_id: equationId }),
    ]);
    rowMap.statusBytes = base64ToBytes(rowMap.status_bytes_b64);
    targetMap.statusBytes = base64ToBytes(targetMap.status_bytes_b64);
    delete rowMap.status_bytes_b64;
    delete targetMap.status_bytes_b64;
    state.rowMap = rowMap;
    state.targetMap = targetMap;
    renderRowMap(rowMap);
    renderTargetMap(targetMap);
  } catch (error) {
    $("rowMapMeta").textContent = "error";
    showToast(error.message);
  } finally {
    $("rowMapButton").disabled = false;
  }
}

function base64ToBytes(raw) {
  const binary = atob(raw);
  const bytes = new Uint8Array(binary.length);
  for (let index = 0; index < binary.length; index += 1) {
    bytes[index] = binary.charCodeAt(index);
  }
  return bytes;
}

function renderRowMapLegend() {
  $("rowMapLegend").innerHTML = Object.values(rowMapCodes)
    .map((item) => `<span class="legend-item"><span style="background:${item.color}"></span>${item.label}</span>`)
    .join("");
}

function renderRowMap(result) {
  renderRowNetwork(result);
  renderRowMapSummary(result);
  const canvas = $("rowMapCanvas");
  const parent = canvas.parentElement;
  const cssWidth = Math.max(320, Math.floor(parent.clientWidth));
  const cell = cssWidth >= 900 ? 2 : 1;
  const columns = Math.max(1, Math.min(result.row_width, Math.floor(cssWidth / cell)));
  const rows = Math.ceil(result.row_width / columns);
  const cssHeight = Math.max(90, rows * cell);
  const ratio = window.devicePixelRatio || 1;
  canvas.style.width = `${cssWidth}px`;
  canvas.style.height = `${cssHeight}px`;
  canvas.width = Math.floor(cssWidth * ratio);
  canvas.height = Math.floor(cssHeight * ratio);
  const ctx = canvas.getContext("2d");
  ctx.setTransform(ratio, 0, 0, ratio, 0, 0);
  ctx.clearRect(0, 0, cssWidth, cssHeight);
  for (let slot = 0; slot < result.statusBytes.length; slot += 1) {
    const code = result.statusBytes[slot];
    const x = (slot % columns) * cell;
    const y = Math.floor(slot / columns) * cell;
    ctx.fillStyle = rowMapCodes[code]?.color || layerColors.unknown;
    ctx.fillRect(x, y, cell, cell);
  }
  state.rowMapLayout = { cell, columns, cssWidth, cssHeight };
  renderFlowMeta();
}

function renderRowMapSummary(result) {
  renderStatusSummary("rowMapSummary", result, result.row_width);
}

function renderTargetMapSummary(result) {
  renderStatusSummary("targetMapSummary", result, result.column_width);
}

function renderStatusSummary(elementId, result, total) {
  const denominator = total || 1;
  $(elementId).innerHTML = Object.values(rowMapCodes)
    .map((item) => {
      const count = result.counts[item.label] || 0;
      const percent = (count / denominator) * 100;
      return `
        <div class="map-summary-item">
          <span class="summary-swatch" style="background:${item.color}"></span>
          <span>${item.label}</span>
          <strong>${formatInt(count)}</strong>
          <em>${percent.toFixed(count && percent < 0.1 ? 3 : 2)}%</em>
        </div>
      `;
    })
    .join("");
}

function renderTargetMap(result) {
  renderTargetNetwork(result);
  renderTargetMapSummary(result);
  const canvas = $("targetMapCanvas");
  const parent = canvas.parentElement;
  const cssWidth = Math.max(320, Math.floor(parent.clientWidth));
  const cell = cssWidth >= 900 ? 2 : 1;
  const columns = Math.max(1, Math.min(result.column_width, Math.floor(cssWidth / cell)));
  const rows = Math.ceil(result.column_width / columns);
  const cssHeight = Math.max(90, rows * cell);
  const ratio = window.devicePixelRatio || 1;
  canvas.style.width = `${cssWidth}px`;
  canvas.style.height = `${cssHeight}px`;
  canvas.width = Math.floor(cssWidth * ratio);
  canvas.height = Math.floor(cssHeight * ratio);
  const ctx = canvas.getContext("2d");
  ctx.setTransform(ratio, 0, 0, ratio, 0, 0);
  ctx.clearRect(0, 0, cssWidth, cssHeight);
  for (let slot = 0; slot < result.statusBytes.length; slot += 1) {
    const code = result.statusBytes[slot];
    const x = (slot % columns) * cell;
    const y = Math.floor(slot / columns) * cell;
    ctx.fillStyle = rowMapCodes[code]?.color || layerColors.unknown;
    ctx.fillRect(x, y, cell, cell);
  }
  state.targetMapLayout = { cell, columns, cssWidth, cssHeight };
  renderFlowMeta();
}

function renderFlowMeta() {
  const parts = [];
  if (state.rowMap) {
    const known = state.rowMap.row_width - (state.rowMap.counts.unknown || 0);
    parts.push(`source ${state.rowMap.source_id}: known ${formatInt(known)}, unknown ${formatInt(state.rowMap.counts.unknown)}`);
  }
  if (state.targetMap) {
    const known = state.targetMap.column_width - (state.targetMap.counts.unknown || 0);
    parts.push(`target ${state.targetMap.target_id}: known ${formatInt(known)}, unknown ${formatInt(state.targetMap.counts.unknown)}`);
  }
  $("rowMapMeta").textContent = parts.join(" | ") || "idle";
}

function renderRowNetwork(result) {
  const canvas = $("rowNetworkCanvas");
  const parent = canvas.parentElement;
  const cssWidth = Math.max(320, Math.floor(parent.clientWidth));
  const cssHeight = cssWidth >= 900 ? 260 : 220;
  const ratio = window.devicePixelRatio || 1;
  canvas.style.width = `${cssWidth}px`;
  canvas.style.height = `${cssHeight}px`;
  canvas.width = Math.floor(cssWidth * ratio);
  canvas.height = Math.floor(cssHeight * ratio);
  const ctx = canvas.getContext("2d");
  ctx.setTransform(ratio, 0, 0, ratio, 0, 0);
  ctx.clearRect(0, 0, cssWidth, cssHeight);
  drawNetworkBackground(ctx, cssWidth, cssHeight);

  const source = { x: 72, y: cssHeight / 2, radius: 25 };
  const targetArea = {
    left: Math.min(230, cssWidth * 0.28),
    right: cssWidth - 34,
    top: 34,
    bottom: cssHeight - 34,
  };
  const nodes = buildNetworkNodes(result, targetArea);
  drawNetworkLinks(ctx, source, nodes);
  drawNetworkNodes(ctx, nodes);
  drawSourceNode(ctx, source, result.source_id);
  drawNetworkLabels(ctx, cssWidth, cssHeight, nodes.length);
  state.rowNetworkLayout = { source, nodes, cssWidth, cssHeight };
}

function renderTargetNetwork(result) {
  const canvas = $("targetNetworkCanvas");
  const parent = canvas.parentElement;
  const cssWidth = Math.max(320, Math.floor(parent.clientWidth));
  const cssHeight = cssWidth >= 900 ? 260 : 220;
  const ratio = window.devicePixelRatio || 1;
  canvas.style.width = `${cssWidth}px`;
  canvas.style.height = `${cssHeight}px`;
  canvas.width = Math.floor(cssWidth * ratio);
  canvas.height = Math.floor(cssHeight * ratio);
  const ctx = canvas.getContext("2d");
  ctx.setTransform(ratio, 0, 0, ratio, 0, 0);
  ctx.clearRect(0, 0, cssWidth, cssHeight);
  drawNetworkBackground(ctx, cssWidth, cssHeight);

  const target = { x: cssWidth - 72, y: cssHeight / 2, radius: 25 };
  const sourceArea = {
    left: 34,
    right: Math.max(cssWidth - 230, cssWidth * 0.72),
    top: 34,
    bottom: cssHeight - 34,
  };
  const nodes = buildIncomingNetworkNodes(result, sourceArea);
  drawIncomingNetworkLinks(ctx, nodes, target);
  drawNetworkNodes(ctx, nodes);
  drawTargetNode(ctx, target, result.target_id);
  drawTargetNetworkLabels(ctx, cssWidth, cssHeight, nodes.length);
  state.targetNetworkLayout = { target, nodes, cssWidth, cssHeight };
}

function drawNetworkBackground(ctx, width, height) {
  const gradient = ctx.createLinearGradient(0, 0, width, height);
  gradient.addColorStop(0, "#f7fafa");
  gradient.addColorStop(1, "#f1f4f5");
  ctx.fillStyle = gradient;
  ctx.fillRect(0, 0, width, height);
  ctx.strokeStyle = "#dbe2e5";
  ctx.lineWidth = 1;
  for (let index = 0; index < 6; index += 1) {
    const y = 34 + ((height - 68) * index) / 5;
    ctx.beginPath();
    ctx.moveTo(170, y);
    ctx.lineTo(width - 34, y);
    ctx.stroke();
  }
}

function buildNetworkNodes(result, targetArea) {
  const slotsByCode = new Map();
  for (let code = 0; code <= 6; code += 1) slotsByCode.set(code, []);
  for (let slot = 0; slot < result.statusBytes.length; slot += 1) {
    slotsByCode.get(result.statusBytes[slot]).push(slot);
  }
  const budgets = [
    [3, 70],
    [0, 120],
    [1, 70],
    [4, 50],
    [5, 50],
    [6, 40],
    [2, 42],
  ];
  const laneByCode = {
    3: 0.16,
    0: 0.32,
    1: 0.48,
    4: 0.62,
    5: 0.74,
    6: 0.84,
    2: 0.58,
  };
  const nodes = [];
  for (const [code, budget] of budgets) {
    const sampled = sampleEvenly(slotsByCode.get(code), budget);
    for (const slot of sampled) {
      const targetId = targetIdFromRowSlot(slot, result);
      const normalized = Math.max(0, Math.min(1, (targetId - 1) / Math.max(1, result.law_count - 1)));
      const jitter = deterministicJitter(slot);
      const lane = laneByCode[code] ?? 0.5;
      nodes.push({
        slot,
        targetId,
        code,
        label: rowMapCodes[code]?.label || "unknown",
        x: targetArea.left + normalized * (targetArea.right - targetArea.left),
        y: targetArea.top + lane * (targetArea.bottom - targetArea.top) + jitter * 18,
        radius: code === 3 ? 4.6 : code === 0 ? 3.8 : code === 2 ? 2.6 : 3.2,
      });
    }
  }
  return nodes.sort((left, right) => left.x - right.x || left.y - right.y);
}

function buildIncomingNetworkNodes(result, sourceArea) {
  const slotsByCode = new Map();
  for (let code = 0; code <= 6; code += 1) slotsByCode.set(code, []);
  for (let slot = 0; slot < result.statusBytes.length; slot += 1) {
    slotsByCode.get(result.statusBytes[slot]).push(slot);
  }
  const budgets = [
    [3, 70],
    [0, 120],
    [1, 70],
    [4, 50],
    [5, 50],
    [6, 40],
    [2, 42],
  ];
  const laneByCode = {
    3: 0.16,
    0: 0.32,
    1: 0.48,
    4: 0.62,
    5: 0.74,
    6: 0.84,
    2: 0.58,
  };
  const nodes = [];
  for (const [code, budget] of budgets) {
    const sampled = sampleEvenly(slotsByCode.get(code), budget);
    for (const slot of sampled) {
      const sourceId = sourceIdFromTargetSlot(slot, result);
      const normalized = Math.max(0, Math.min(1, (sourceId - 1) / Math.max(1, result.law_count - 1)));
      const jitter = deterministicJitter(slot + result.target_id * 17);
      const lane = laneByCode[code] ?? 0.5;
      nodes.push({
        slot,
        sourceId,
        code,
        label: rowMapCodes[code]?.label || "unknown",
        x: sourceArea.left + normalized * (sourceArea.right - sourceArea.left),
        y: sourceArea.top + lane * (sourceArea.bottom - sourceArea.top) + jitter * 18,
        radius: code === 3 ? 4.6 : code === 0 ? 3.8 : code === 2 ? 2.6 : 3.2,
      });
    }
  }
  return nodes.sort((left, right) => left.x - right.x || left.y - right.y);
}

function sampleEvenly(items, budget) {
  if (!items || items.length <= budget) return items || [];
  const sampled = [];
  const step = (items.length - 1) / Math.max(1, budget - 1);
  for (let index = 0; index < budget; index += 1) {
    sampled.push(items[Math.round(index * step)]);
  }
  return sampled;
}

function deterministicJitter(value) {
  const raw = Math.sin(value * 12.9898) * 43758.5453;
  return (raw - Math.floor(raw)) * 2 - 1;
}

function drawNetworkLinks(ctx, source, nodes) {
  for (const node of nodes) {
    const color = rowMapCodes[node.code]?.color || layerColors.unknown;
    ctx.strokeStyle = hexToRgba(color, node.code === 0 ? 0.42 : node.code === 2 ? 0.16 : 0.32);
    ctx.lineWidth = node.code === 3 ? 1.4 : node.code === 0 ? 1.0 : 0.8;
    const controlOneX = source.x + (node.x - source.x) * 0.34;
    const controlTwoX = source.x + (node.x - source.x) * 0.72;
    const bend = (node.y - source.y) * 0.18;
    ctx.beginPath();
    ctx.moveTo(source.x + source.radius - 2, source.y);
    ctx.bezierCurveTo(controlOneX, source.y - bend, controlTwoX, node.y + bend, node.x, node.y);
    ctx.stroke();
  }
}

function drawIncomingNetworkLinks(ctx, nodes, target) {
  for (const node of nodes) {
    const color = rowMapCodes[node.code]?.color || layerColors.unknown;
    ctx.strokeStyle = hexToRgba(color, node.code === 0 ? 0.42 : node.code === 2 ? 0.16 : 0.32);
    ctx.lineWidth = node.code === 3 ? 1.4 : node.code === 0 ? 1.0 : 0.8;
    const controlOneX = node.x + (target.x - node.x) * 0.28;
    const controlTwoX = node.x + (target.x - node.x) * 0.66;
    const bend = (target.y - node.y) * 0.18;
    ctx.beginPath();
    ctx.moveTo(node.x, node.y);
    ctx.bezierCurveTo(controlOneX, node.y + bend, controlTwoX, target.y - bend, target.x - target.radius + 2, target.y);
    ctx.stroke();
  }
}

function drawNetworkNodes(ctx, nodes) {
  for (const node of nodes) {
    ctx.beginPath();
    ctx.fillStyle = rowMapCodes[node.code]?.color || layerColors.unknown;
    ctx.strokeStyle = "#ffffff";
    ctx.lineWidth = 1.5;
    ctx.arc(node.x, node.y, node.radius, 0, Math.PI * 2);
    ctx.fill();
    ctx.stroke();
  }
}

function drawSourceNode(ctx, source, sourceId) {
  ctx.beginPath();
  ctx.fillStyle = "#1f5f88";
  ctx.strokeStyle = "#ffffff";
  ctx.lineWidth = 3;
  ctx.arc(source.x, source.y, source.radius, 0, Math.PI * 2);
  ctx.fill();
  ctx.stroke();
  ctx.fillStyle = "#ffffff";
  ctx.font = "700 13px system-ui, sans-serif";
  ctx.textAlign = "center";
  ctx.textBaseline = "middle";
  ctx.fillText(String(sourceId), source.x, source.y);
}

function drawTargetNode(ctx, target, targetId) {
  ctx.beginPath();
  ctx.fillStyle = "#1f5f88";
  ctx.strokeStyle = "#ffffff";
  ctx.lineWidth = 3;
  ctx.arc(target.x, target.y, target.radius, 0, Math.PI * 2);
  ctx.fill();
  ctx.stroke();
  ctx.fillStyle = "#ffffff";
  ctx.font = "700 13px system-ui, sans-serif";
  ctx.textAlign = "center";
  ctx.textBaseline = "middle";
  ctx.fillText(String(targetId), target.x, target.y);
}

function drawNetworkLabels(ctx, width, height, nodeCount) {
  ctx.fillStyle = "#536069";
  ctx.font = "12px system-ui, sans-serif";
  ctx.textAlign = "left";
  ctx.fillText("source", 48, height / 2 + 42);
  ctx.textAlign = "right";
  ctx.fillText(`${nodeCount} sampled target links`, width - 34, 22);
}

function drawTargetNetworkLabels(ctx, width, height, nodeCount) {
  ctx.fillStyle = "#536069";
  ctx.font = "12px system-ui, sans-serif";
  ctx.textAlign = "left";
  ctx.fillText(`${nodeCount} sampled source links`, 34, 22);
  ctx.textAlign = "right";
  ctx.fillText("target", width - 48, height / 2 + 42);
}

function hexToRgba(hex, alpha) {
  const clean = hex.replace("#", "");
  const value = parseInt(clean.length === 3 ? clean.split("").map((char) => char + char).join("") : clean, 16);
  const r = (value >> 16) & 255;
  const g = (value >> 8) & 255;
  const b = value & 255;
  return `rgba(${r}, ${g}, ${b}, ${alpha})`;
}

function rowMapSlotFromEvent(event) {
  if (!state.rowMap || !state.rowMapLayout) return null;
  const canvas = $("rowMapCanvas");
  const rect = canvas.getBoundingClientRect();
  const x = event.clientX - rect.left;
  const y = event.clientY - rect.top;
  if (x < 0 || y < 0 || x > rect.width || y > rect.height) return null;
  const { cell, columns } = state.rowMapLayout;
  const slot = Math.floor(y / cell) * columns + Math.floor(x / cell);
  if (slot < 0 || slot >= state.rowMap.row_width) return null;
  return slot;
}

function targetMapSlotFromEvent(event) {
  if (!state.targetMap || !state.targetMapLayout) return null;
  const canvas = $("targetMapCanvas");
  const rect = canvas.getBoundingClientRect();
  const x = event.clientX - rect.left;
  const y = event.clientY - rect.top;
  if (x < 0 || y < 0 || x > rect.width || y > rect.height) return null;
  const { cell, columns } = state.targetMapLayout;
  const slot = Math.floor(y / cell) * columns + Math.floor(x / cell);
  if (slot < 0 || slot >= state.targetMap.column_width) return null;
  return slot;
}

function rowNetworkNodeFromEvent(event) {
  if (!state.rowNetworkLayout) return null;
  const canvas = $("rowNetworkCanvas");
  const rect = canvas.getBoundingClientRect();
  const x = event.clientX - rect.left;
  const y = event.clientY - rect.top;
  let best = null;
  let bestDistance = Infinity;
  for (const node of state.rowNetworkLayout.nodes) {
    const dx = node.x - x;
    const dy = node.y - y;
    const distance = Math.sqrt(dx * dx + dy * dy);
    if (distance < Math.max(7, node.radius + 4) && distance < bestDistance) {
      best = node;
      bestDistance = distance;
    }
  }
  return best;
}

function targetNetworkNodeFromEvent(event) {
  if (!state.targetNetworkLayout) return null;
  const canvas = $("targetNetworkCanvas");
  const rect = canvas.getBoundingClientRect();
  const x = event.clientX - rect.left;
  const y = event.clientY - rect.top;
  let best = null;
  let bestDistance = Infinity;
  for (const node of state.targetNetworkLayout.nodes) {
    const dx = node.x - x;
    const dy = node.y - y;
    const distance = Math.sqrt(dx * dx + dy * dy);
    if (distance < Math.max(7, node.radius + 4) && distance < bestDistance) {
      best = node;
      bestDistance = distance;
    }
  }
  return best;
}

function targetIdFromRowSlot(slot, rowMap) {
  if (rowMap.include_self) return slot + 1;
  return slot < rowMap.source_id - 1 ? slot + 1 : slot + 2;
}

function sourceIdFromTargetSlot(slot, targetMap) {
  if (targetMap.include_self) return slot + 1;
  return slot < targetMap.target_id - 1 ? slot + 1 : slot + 2;
}

function moveRowMapTooltip(event) {
  const tooltip = $("rowMapTooltip");
  const slot = rowMapSlotFromEvent(event);
  if (slot === null) {
    tooltip.hidden = true;
    return;
  }
  const code = state.rowMap.statusBytes[slot];
  const targetId = targetIdFromRowSlot(slot, state.rowMap);
  tooltip.textContent = `${state.rowMap.source_id} -> ${targetId} | ${rowMapCodes[code]?.label || "unknown"}`;
  tooltip.hidden = false;
  const sectionRect = document.querySelector(".row-map-section").getBoundingClientRect();
  tooltip.style.left = `${event.clientX - sectionRect.left + 12}px`;
  tooltip.style.top = `${event.clientY - sectionRect.top + 12}px`;
}

function moveTargetMapTooltip(event) {
  const tooltip = $("rowMapTooltip");
  const slot = targetMapSlotFromEvent(event);
  if (slot === null) {
    tooltip.hidden = true;
    return;
  }
  const code = state.targetMap.statusBytes[slot];
  const sourceId = sourceIdFromTargetSlot(slot, state.targetMap);
  tooltip.textContent = `${sourceId} -> ${state.targetMap.target_id} | ${rowMapCodes[code]?.label || "unknown"}`;
  tooltip.hidden = false;
  const sectionRect = document.querySelector(".row-map-section").getBoundingClientRect();
  tooltip.style.left = `${event.clientX - sectionRect.left + 12}px`;
  tooltip.style.top = `${event.clientY - sectionRect.top + 12}px`;
}

function moveRowNetworkTooltip(event) {
  const tooltip = $("rowMapTooltip");
  const node = rowNetworkNodeFromEvent(event);
  if (!node || !state.rowMap) {
    tooltip.hidden = true;
    return;
  }
  tooltip.textContent = `${state.rowMap.source_id} -> ${node.targetId} | ${node.label}`;
  tooltip.hidden = false;
  const sectionRect = document.querySelector(".row-map-section").getBoundingClientRect();
  tooltip.style.left = `${event.clientX - sectionRect.left + 12}px`;
  tooltip.style.top = `${event.clientY - sectionRect.top + 12}px`;
}

function moveTargetNetworkTooltip(event) {
  const tooltip = $("rowMapTooltip");
  const node = targetNetworkNodeFromEvent(event);
  if (!node || !state.targetMap) {
    tooltip.hidden = true;
    return;
  }
  tooltip.textContent = `${node.sourceId} -> ${state.targetMap.target_id} | ${node.label}`;
  tooltip.hidden = false;
  const sectionRect = document.querySelector(".row-map-section").getBoundingClientRect();
  tooltip.style.left = `${event.clientX - sectionRect.left + 12}px`;
  tooltip.style.top = `${event.clientY - sectionRect.top + 12}px`;
}

function clickRowMap(event) {
  const slot = rowMapSlotFromEvent(event);
  if (slot === null) return;
  const targetId = targetIdFromRowSlot(slot, state.rowMap);
  $("pairSource").value = state.rowMap.source_id;
  $("pairTarget").value = targetId;
  queryPair();
}

function clickTargetMap(event) {
  const slot = targetMapSlotFromEvent(event);
  if (slot === null) return;
  const sourceId = sourceIdFromTargetSlot(slot, state.targetMap);
  $("pairSource").value = sourceId;
  $("pairTarget").value = state.targetMap.target_id;
  queryPair();
}

function clickRowNetwork(event) {
  const node = rowNetworkNodeFromEvent(event);
  if (!node || !state.rowMap) return;
  $("pairSource").value = state.rowMap.source_id;
  $("pairTarget").value = node.targetId;
  queryPair();
}

function clickTargetNetwork(event) {
  const node = targetNetworkNodeFromEvent(event);
  if (!node || !state.targetMap) return;
  $("pairSource").value = node.sourceId;
  $("pairTarget").value = state.targetMap.target_id;
  queryPair();
}

async function queryPair() {
  const params = {
    source_id: $("pairSource").value.trim(),
    target_id: $("pairTarget").value.trim(),
  };
  try {
    const result = await fetchJson("/api/status", params);
    renderPair(result);
  } catch (error) {
    showToast(error.message);
  }
}

function renderPair(result) {
  $("pairVerdict").textContent = result.verdict;
  const layers = Object.entries(result.layers)
    .map(([name, enabled]) => `<span class="chip ${enabled ? name : "off"}">${name}: ${enabled ? "on" : "off"}</span>`)
    .join("");
  $("pairResult").innerHTML = `
    <div class="status-grid">${layers}</div>
    <div class="layer-stat">${result.eq1_id} -> ${result.eq2_id}</div>
    ${renderEquations(result.equations)}
  `;
}

function renderEquations(equations) {
  if (!equations || (!equations.source && !equations.target)) return "";
  return `
    <div class="equation-block">
      <div class="equation">${equations.source || ""}</div>
      <div class="equation">${equations.target || ""}</div>
    </div>
  `;
}

async function queryRow(action = state.rowAction) {
  state.rowAction = action;
  document.querySelectorAll("[data-row-action]").forEach((button) => {
    button.classList.toggle("active", button.dataset.rowAction === action);
  });
  const sourceId = $("rowSource").value.trim();
  const limit = $("rowLimit").value.trim();
  $("rowSourcePill").textContent = `source ${sourceId || "?"}`;
  try {
    if (action === "summary") {
      renderRowSummary(await fetchJson("/api/row-summary", { source_id: sourceId }));
    } else if (action === "frontier") {
      renderFrontier(await fetchJson("/api/frontier", { source_id: sourceId, limit }));
    } else {
      renderTargets(await fetchJson("/api/row-targets", {
        source_id: sourceId,
        limit,
        layer: $("rowLayer").value,
      }));
    }
  } catch (error) {
    showToast(error.message);
  }
}

function renderRowSummary(result) {
  const counts = Object.entries(result.layer_counts)
    .map(([name, count]) => {
      const percent = result.row_width ? (count / result.row_width) * 100 : 0;
      return `
        <tr>
          <td>${name}</td>
          <td class="num">${formatInt(count)}</td>
          <td>
            <div class="bar"><div class="bar-fill" style="width:${Math.max(percent, count > 0 ? 1 : 0)}%;background:${layerColors[name] || "#286da8"}"></div></div>
          </td>
        </tr>
      `;
    })
    .join("");
  $("rowResult").innerHTML = `
    <table>
      <tbody>
        ${counts}
        <tr><td>exact_known</td><td class="num">${formatInt(result.exact_known_count)}</td><td></td></tr>
        <tr><td>unknown</td><td class="num">${formatInt(result.unknown_count)}</td><td></td></tr>
      </tbody>
    </table>
  `;
}

function renderFrontier(result) {
  $("rowResult").innerHTML = `
    <div class="layer-stat">unknown ${formatInt(result.unknown_count)}</div>
    <div class="target-list">
      ${result.targets.map((target) => targetButton(result.source_id, target)).join("")}
    </div>
  `;
  wireTargetButtons();
}

function renderTargets(result) {
  $("rowResult").innerHTML = `
    <div class="layer-stat">${result.layer} targets, limit ${formatInt(result.limit)}</div>
    <div class="target-list">
      ${result.targets.map((target) => targetButton(result.source_id, target)).join("")}
    </div>
  `;
  wireTargetButtons();
}

function targetButton(source, target) {
  return `<button type="button" data-source="${source}" data-target="${target}">${target}</button>`;
}

function wireTargetButtons() {
  document.querySelectorAll("[data-source][data-target]").forEach((button) => {
    button.addEventListener("click", () => {
      $("pairSource").value = button.dataset.source;
      $("pairTarget").value = button.dataset.target;
      queryPair();
    });
  });
}

function boot() {
  $("countBitsButton").addEventListener("click", () => refreshSummary({ countBits: true }));
  $("pairQueryButton").addEventListener("click", queryPair);
  $("rowMapButton").addEventListener("click", queryRowMap);
  $("rowMapCanvas").addEventListener("mousemove", moveRowMapTooltip);
  $("rowMapCanvas").addEventListener("mouseleave", () => {
    $("rowMapTooltip").hidden = true;
  });
  $("rowMapCanvas").addEventListener("click", clickRowMap);
  $("targetMapCanvas").addEventListener("mousemove", moveTargetMapTooltip);
  $("targetMapCanvas").addEventListener("mouseleave", () => {
    $("rowMapTooltip").hidden = true;
  });
  $("targetMapCanvas").addEventListener("click", clickTargetMap);
  $("rowNetworkCanvas").addEventListener("mousemove", moveRowNetworkTooltip);
  $("rowNetworkCanvas").addEventListener("mouseleave", () => {
    $("rowMapTooltip").hidden = true;
  });
  $("rowNetworkCanvas").addEventListener("click", clickRowNetwork);
  $("targetNetworkCanvas").addEventListener("mousemove", moveTargetNetworkTooltip);
  $("targetNetworkCanvas").addEventListener("mouseleave", () => {
    $("rowMapTooltip").hidden = true;
  });
  $("targetNetworkCanvas").addEventListener("click", clickTargetNetwork);
  window.addEventListener("resize", () => {
    if (state.rowMap) renderRowMap(state.rowMap);
    if (state.targetMap) renderTargetMap(state.targetMap);
  });
  refreshSummary();
  queryRowMap();
}

boot();
