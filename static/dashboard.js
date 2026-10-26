const state = { coins: [], selected: null };

const money = new Intl.NumberFormat("en-US", { style: "currency", currency: "USD", maximumFractionDigits: 2 });
const compact = new Intl.NumberFormat("en-US", { notation: "compact", maximumFractionDigits: 2 });

function showToast(message, isError = false) {
  const toast = document.getElementById("toast");
  toast.textContent = message;
  toast.className = `toast show${isError ? " error" : ""}`;
  window.setTimeout(() => { toast.className = "toast"; }, 3200);
}

async function loadMarket() {
  const selectedId = state.selected;
  try {
    const params = selectedId ? `?coin_id=${encodeURIComponent(selectedId)}` : "";
    const response = await fetch(`/api/market${params}`);
    if (!response.ok) throw new Error(`Market request failed (${response.status})`);
    const data = await response.json();
    state.coins = data.coins;

    document.getElementById("coinCount").textContent = data.summary.coin_count.toLocaleString("en-US");
    document.getElementById("marketCap").textContent = `$${compact.format(data.summary.market_cap)}`;
    document.getElementById("volume").textContent = `$${compact.format(data.summary.volume_24h)}`;

    if (data.summary.last_updated) {
      const date = new Date(data.summary.last_updated);
      document.getElementById("lastUpdate").textContent = date.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
      document.getElementById("updateDetail").textContent = date.toLocaleDateString([], { month: "short", day: "numeric", year: "numeric" });
    } else {
      document.getElementById("lastUpdate").textContent = "--";
      document.getElementById("updateDetail").textContent = "Waiting for data";
    }

    renderMovers(data.coins);
    renderTable(data.coins);

    if (selectedId) {
      const selected = data.coins.find((coin) => coin.coin_id === selectedId);
      if (selected) updateChart(selected, data.history);
    } else if (data.coins.length) {
      selectCoin(data.coins[0]);
    } else {
      renderEmptyChart();
    }
  } catch (error) {
    showToast(error.message, true);
    renderEmptyChart();
  }
}

function renderMovers(coins) {
  const sorted = [...coins].sort((a, b) => (b.price_change_24h || 0) - (a.price_change_24h || 0));
  const movers = document.getElementById("movers");
  movers.innerHTML = "";

  sorted.slice(0, 4).forEach((coin) => {
    const change = Number(coin.price_change_24h || 0);
    const row = document.createElement("div");
    row.className = "mover";
    row.innerHTML = `
      <span class="coin-avatar">${coin.symbol.slice(0, 3).toUpperCase()}</span>
      <span class="mover-name"><strong>${coin.name}</strong><small>${coin.symbol.toUpperCase()}</small></span>
      <span class="change ${change >= 0 ? "positive" : "negative"}">${change >= 0 ? "+" : ""}${change.toFixed(2)}%</span>`;
    movers.appendChild(row);
  });
}

function renderTable(coins) {
  const tbody = document.getElementById("assetRows");
  tbody.innerHTML = "";
  coins.forEach((coin) => {
    const change = Number(coin.price_change_24h || 0);
    const row = document.createElement("tr");
    row.innerHTML = `
      <td><div class="asset-cell"><span class="coin-avatar">${coin.symbol.slice(0, 3).toUpperCase()}</span><span><strong>${coin.name}</strong><small>${coin.coin_id}</small></span></div></td>
      <td>${money.format(coin.price_usd)}</td>
      <td><span class="change ${change >= 0 ? "positive" : "negative"}">${change >= 0 ? "+" : ""}${change.toFixed(2)}%</span></td>
      <td>$${compact.format(coin.market_cap_usd || 0)}</td>
      <td>$${compact.format(coin.total_volume_usd || 0)}</td>
      <td><button class="view-button" type="button" data-coin="${coin.coin_id}" aria-label="View ${coin.name}">›</button></td>`;
    tbody.appendChild(row);
  });

  if (!coins.length) {
    tbody.innerHTML = `<tr><td colspan="6" style="text-align:center;color:#71766f">No assets available. Refresh the market data.</td></tr>`;
  }
}

async function selectCoin(coin) {
  state.selected = coin.coin_id;
  try {
    const response = await fetch(`/api/market?coin_id=${encodeURIComponent(coin.coin_id)}`);
    if (!response.ok) throw new Error("Could not load asset history");
    const data = await response.json();
    updateChart(coin, data.history);
  } catch (error) {
    showToast(error.message, true);
  }
}

function updateChart(coin, history) {
  document.getElementById("chartTitle").textContent = `${coin.name} / ${coin.symbol.toUpperCase()}`;
  document.getElementById("chartPrice").textContent = money.format(coin.price_usd);
  renderChart(history);
}

function renderEmptyChart() {
  document.getElementById("chartTitle").textContent = "Select an asset";
  document.getElementById("chartPrice").textContent = "--";
  document.getElementById("emptyChart").classList.remove("hidden");
  document.getElementById("priceChart").replaceChildren();
}

function renderChart(history) {
  const svg = document.getElementById("priceChart");
  const empty = document.getElementById("emptyChart");
  if (!history.length) {
    empty.classList.remove("hidden");
    svg.replaceChildren();
    return;
  }
  empty.classList.add("hidden");

  const width = 760;
  const height = 280;
  const left = 56;
  const right = 18;
  const top = 18;
  const bottom = 34;
  const prices = history.map((item) => Number(item.price));
  const min = Math.min(...prices);
  const max = Math.max(...prices);
  const spread = max - min || max * 0.05 || 1;
  const x = (index) => history.length === 1 ? width / 2 : left + index * ((width - left - right) / (history.length - 1));
  const y = (price) => top + ((max + spread * 0.08 - price) / (spread * 1.16)) * (height - top - bottom);

  const gridColor = "#d9d4c7";
  const lineColor = "#207d5a";
  let markup = `<rect width="${width}" height="${height}" fill="#fffdf7"/>`;
  for (let index = 0; index < 5; index += 1) {
    const gridY = top + index * ((height - top - bottom) / 4);
    const value = max + spread * 0.08 - index * ((spread * 1.16) / 4);
    markup += `<line x1="${left}" x2="${width-right}" y1="${gridY}" y2="${gridY}" stroke="${gridColor}" stroke-width="1"/>`;
    markup += `<text x="${left-10}" y="${gridY+4}" text-anchor="end" fill="#71766f" font-size="10" font-family="Arial">${compact.format(value)}</text>`;
  }

  const points = history.map((item, index) => `${x(index)},${y(Number(item.price))}`).join(" ");
  const linePath = history.map((item, index) => `${index === 0 ? "M" : "L"}${x(index)},${y(Number(item.price))}`).join(" ");
  const baseline = height - bottom;
  markup += `<polygon points="${left},${baseline} ${points} ${width-right},${baseline}" fill="#207d5a" fill-opacity=".08"/>`;
  markup += `<path d="${linePath}" fill="none" stroke="${lineColor}" stroke-width="3" stroke-linejoin="round" stroke-linecap="round"/>`;

  const labelIndexes = [...new Set([0, Math.floor((history.length-1)/2), history.length-1])];
  labelIndexes.forEach((index) => {
    const date = new Date(history[index].timestamp);
    markup += `<text x="${x(index)}" y="${height-10}" text-anchor="middle" fill="#71766f" font-size="10" font-family="Arial">${date.toLocaleDateString([], { month: "short", day: "numeric" })}</text>`;
  });

  const lastIndex = history.length - 1;
  markup += `<circle cx="${x(lastIndex)}" cy="${y(prices[lastIndex])}" r="5" fill="#fffdf7" stroke="${lineColor}" stroke-width="3"/>`;
  svg.innerHTML = markup;
}

document.getElementById("refreshButton").addEventListener("click", async (event) => {
  const button = event.currentTarget;
  button.disabled = true;
  button.classList.add("loading");
  try {
    const response = await fetch("/api/refresh", { method: "POST" });
    const data = await response.json();
    if (!response.ok || !data.ok) throw new Error(data.message || "Refresh failed");
    showToast(data.message);
    await loadMarket();
  } catch (error) {
    showToast(error.message, true);
  } finally {
    button.disabled = false;
    button.classList.remove("loading");
  }
});

document.getElementById("assetSearch").addEventListener("input", (event) => {
  const query = event.target.value.trim().toLowerCase();
  document.querySelectorAll("#assetRows tr").forEach((row) => {
    row.hidden = query && !row.textContent.toLowerCase().includes(query);
  });
});

document.getElementById("assetRows").addEventListener("click", (event) => {
  const button = event.target.closest("[data-coin]");
  if (!button) return;
  const coin = state.coins.find((item) => item.coin_id === button.dataset.coin);
  if (coin) selectCoin(coin);
});

document.getElementById("todayLabel").textContent = new Date().toLocaleDateString("en-US", { weekday: "long", month: "long", day: "numeric" });
loadMarket();
