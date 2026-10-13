let genreDistChartInstance = null;
let genrePopChartInstance = null;
let quarantineChartInstance = null;
let currentExtractedMetadata = null;
let pipelinePollInterval = null;

let cachedTopArtists = [];
let cachedTopTracks = [];
let cachedCatalogIndex = { popular_tracks: [], top_artists: [] };
let liveSearchTracks = null;
let liveSearchArtists = null;
let searchDebounceTimer = null;
let activeSort = "popularity";
let activeGenreFilter = "ALL";
let searchQuery = "";

// Ensure landing starts cleanly at top without restoring stale scroll offset
if ('scrollRestoration' in history) {
    history.scrollRestoration = 'manual';
}

// Clean obsolete anchor hashes (e.g. #section-pig from old sessions) and ensure landing is at top
if (window.location.hash) {
    const validSections = [
        '#section-top-artists',
        '#section-top-tracks',
        '#section-genre-analytics',
        '#section-lake-layers',
        '#section-quarantine-audit'
    ];
    if (!validSections.includes(window.location.hash)) {
        history.replaceState(null, "", window.location.pathname);
        window.scrollTo(0, 0);
    }
}

document.addEventListener("DOMContentLoaded", async () => {
    // If no explicit valid hash requested, ensure viewport starts at top of landing
    if (!window.location.hash) {
        window.scrollTo(0, 0);
    }

    try {
        await loadDashboardData();
    } catch (err) {
        console.error("Error loading dashboard data:", err);
    }

    initControls();
    initHeroBoxRedirects();
    initHeroFoldCTA();
    initIngestionModal();
    initCookieBanner();
    initTrackSpotlight();
    checkInitialPipelineStatus();
});

async function fetchJSON(url) {
    const res = await fetch(url);
    if (!res.ok) {
        throw new Error(`Failed to load ${url}: ${res.statusText}`);
    }
    return await res.json();
}

async function loadDashboardData() {
    // 1. Fetch authentic result files from pipeline outputs
    const ingestionMetrics = await fetchJSON("data/ingestion_metrics.json");
    const dataQualityReport = await fetchJSON("data/data_quality_report.json");
    const genreMetrics = await fetchJSON("data/genre_metrics.json");
    const topArtists = await fetchJSON("data/top_artists.json");
    const topTracks = await fetchJSON("data/top_tracks_per_genre.json");
    const pipelineReport = await fetchJSON("data/pipeline_execution_report.json");

    cachedTopArtists = topArtists || [];
    cachedTopTracks = topTracks || [];

    try {
        const catIdx = await fetchJSON("data/catalog_search_index.json");
        if (catIdx && catIdx.popular_tracks) {
            cachedCatalogIndex = catIdx;
        }
    } catch (e) {
        console.warn("Catalog index load skipped:", e);
    }

    // 2. Populate Hero & KPI Cards
    const totalCount = ingestionMetrics.total_records.toLocaleString();
    const validCount = ingestionMetrics.valid_records.toLocaleString();
    const invalidCount = ingestionMetrics.invalid_records.toLocaleString();
    const qualScore = `${ingestionMetrics.data_quality_score}%`;

    const elHeroTotal = document.getElementById("hero-total-records");
    if (elHeroTotal) elHeroTotal.textContent = totalCount;

    const elHeroQual = document.getElementById("hero-quality-score");
    if (elHeroQual) elHeroQual.textContent = `${qualScore} QUALITY`;

    const elHeroBadge = document.getElementById("hero-badge");
    if (elHeroBadge) elHeroBadge.textContent = `💀 OVER ${totalCount} INGESTED TRACKS`;

    document.getElementById("total-records").textContent = totalCount;
    document.getElementById("valid-records").textContent = validCount;
    document.getElementById("quarantined-records").textContent = invalidCount;
    document.getElementById("quality-score").textContent = qualScore;

    const runDate = new Date(pipelineReport.timestamp || ingestionMetrics.ingestion_timestamp);
    const dateFormatted = runDate.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
    document.getElementById("ingestion-date").textContent = `Last Pipeline Run: ${dateFormatted}`;

    // 3. Render Neo-Brutalist Charts
    renderGenreDistributionChart(genreMetrics);
    renderGenrePopularityChart(genreMetrics);
    renderQuarantineChart(dataQualityReport.data_quality.quarantine_reasons_breakdown);

    // 4. Populate Tables with active filters & sorting
    applyFiltersAndRenderTables();
}

/* ==========================================================================
   Neo-Brutalist Chart.js Rendering
   ========================================================================== */

function renderGenreDistributionChart(genreData) {
    const canvas = document.getElementById("genreDistributionChart");
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (genreDistChartInstance) {
        genreDistChartInstance.destroy();
    }

    const labels = genreData.map(g => g.genre.toUpperCase());
    const data = genreData.map(g => g.total_tracks);

    const colors = [
        "#00C853", "#FF4081", "#2979FF", "#FF6B00", "#7C4DFF",
        "#00E5FF", "#EAB308", "#F43F5E", "#10B981", "#6366F1"
    ];

    genreDistChartInstance = new Chart(ctx, {
        type: "bar",
        data: {
            labels: labels,
            datasets: [{
                label: "Track Volume",
                data: data,
                backgroundColor: colors.slice(0, labels.length),
                borderColor: "#0A0A0A",
                borderWidth: 3,
                borderRadius: 0,
                barPercentage: 0.8
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false },
                tooltip: {
                    backgroundColor: "#0A0A0A",
                    titleFont: { family: "'Space Mono', monospace", size: 12 },
                    bodyFont: { family: "'Space Mono', monospace", size: 12 },
                    borderColor: "#FFD600",
                    borderWidth: 2,
                    displayColors: false,
                    padding: 10
                }
            },
            scales: {
                x: {
                    grid: { display: false },
                    ticks: {
                        color: "#0A0A0A",
                        font: { family: "'Space Mono', monospace", size: 11, weight: "bold" }
                    }
                },
                y: {
                    grid: { color: "rgba(10, 10, 10, 0.08)", lineWidth: 1.5 },
                    ticks: {
                        color: "#0A0A0A",
                        font: { family: "'Space Mono', monospace", size: 11, weight: "bold" }
                    }
                }
            }
        }
    });
}

function renderGenrePopularityChart(genreData) {
    const canvas = document.getElementById("genrePopularityChart");
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (genrePopChartInstance) {
        genrePopChartInstance.destroy();
    }

    const labels = genreData.map(g => g.genre.toUpperCase());
    const data = genreData.map(g => g.avg_popularity);

    genrePopChartInstance = new Chart(ctx, {
        type: "line",
        data: {
            labels: labels,
            datasets: [{
                label: "Avg Popularity",
                data: data,
                borderColor: "#0A0A0A",
                borderWidth: 4,
                backgroundColor: "rgba(255, 107, 0, 0.2)",
                fill: true,
                stepped: false,
                tension: 0.25,
                pointBackgroundColor: "#FF6B00",
                pointBorderColor: "#0A0A0A",
                pointBorderWidth: 3,
                pointRadius: 6,
                pointHoverRadius: 9
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false },
                tooltip: {
                    backgroundColor: "#0A0A0A",
                    titleFont: { family: "'Space Mono', monospace", size: 12 },
                    bodyFont: { family: "'Space Mono', monospace", size: 12 },
                    borderColor: "#FF6B00",
                    borderWidth: 2,
                    displayColors: false,
                    padding: 10
                }
            },
            scales: {
                x: {
                    grid: { display: false },
                    ticks: {
                        color: "#0A0A0A",
                        font: { family: "'Space Mono', monospace", size: 11, weight: "bold" }
                    }
                },
                y: {
                    suggestedMin: 20,
                    suggestedMax: 80,
                    grid: { color: "rgba(10, 10, 10, 0.08)", lineWidth: 1.5 },
                    ticks: {
                        color: "#0A0A0A",
                        font: { family: "'Space Mono', monospace", size: 11, weight: "bold" }
                    }
                }
            }
        }
    });
}

function renderQuarantineChart(reasons) {
    const canvas = document.getElementById("quarantineAuditChart");
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (quarantineChartInstance) {
        quarantineChartInstance.destroy();
    }

    const labels = Object.keys(reasons || {}).map(l => l.replace(/_/g, " ").toUpperCase());
    const data = Object.values(reasons || {});

    quarantineChartInstance = new Chart(ctx, {
        type: "doughnut",
        data: {
            labels: labels,
            datasets: [{
                data: data,
                backgroundColor: [
                    "#B91C1C", "#FF6B00", "#FFD600", "#00C853", "#2979FF", "#7C4DFF"
                ],
                borderColor: "#0A0A0A",
                borderWidth: 3
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: "right",
                    labels: {
                        color: "#0A0A0A",
                        font: { family: "'Space Mono', monospace", size: 11, weight: "bold" },
                        boxWidth: 14,
                        padding: 12
                    }
                },
                tooltip: {
                    backgroundColor: "#0A0A0A",
                    titleFont: { family: "'Space Mono', monospace" },
                    bodyFont: { family: "'Space Mono', monospace" },
                    borderColor: "#B91C1C",
                    borderWidth: 2,
                    padding: 10
                }
            }
        }
    });
}

/* ==========================================================================
   Filtering, Sorting & Table Rendering
   ========================================================================== */

function updateTableSortHeaders() {
    // Artist table header highlights
    const thArtPop = document.getElementById("th-art-pop");
    const thArtDur = document.getElementById("th-art-dur");
    const thArtYear = document.getElementById("th-art-year");

    if (thArtPop) thArtPop.classList.toggle("th-active-sort", activeSort === "popularity");
    if (thArtDur) thArtDur.classList.toggle("th-active-sort", activeSort === "duration");
    if (thArtYear) thArtYear.classList.toggle("th-active-sort", activeSort === "year");

    // Tracks table header highlights
    const thTrkPop = document.getElementById("th-trk-pop");
    const thTrkYear = document.getElementById("th-trk-year");

    if (thTrkPop) thTrkPop.classList.toggle("th-active-sort", activeSort === "popularity");
    if (thTrkYear) thTrkYear.classList.toggle("th-active-sort", activeSort === "year");
}

function applyFiltersAndRenderTables() {
    updateTableSortHeaders();
    renderTopArtistsTable();
    renderTopTracksTable();
}

function renderTopArtistsTable() {
    const tbody = document.querySelector("#top-artists-table tbody");
    if (!tbody) return;
    tbody.innerHTML = "";

    let list = [];
    if (searchQuery) {
        if (liveSearchArtists && liveSearchArtists.length) {
            list = [...liveSearchArtists];
        } else {
            const q = searchQuery.toLowerCase();
            const source = (cachedCatalogIndex.top_artists && cachedCatalogIndex.top_artists.length)
                ? cachedCatalogIndex.top_artists
                : cachedTopArtists;
            list = source.filter(a => a.artist_name.toLowerCase().includes(q));
        }
    } else {
        list = [...cachedTopArtists];
    }

    // Accurate Multi-Column Sorting
    if (activeSort === "popularity") {
        list.sort((a, b) => b.avg_popularity - a.avg_popularity);
    } else if (activeSort === "duration") {
        list.sort((a, b) => b.avg_duration_sec - a.avg_duration_sec);
    } else if (activeSort === "volume") {
        list.sort((a, b) => b.total_tracks - a.total_tracks);
    } else if (activeSort === "year") {
        list.sort((a, b) => (b.latest_year || 2020) - (a.latest_year || 2020) || (b.avg_popularity - a.avg_popularity));
    }

    if (list.length === 0) {
        tbody.innerHTML = `<tr><td colspan="5" style="text-align:center; padding: 20px; font-family: var(--font-mono); font-weight: bold;">NO ARTISTS FOUND MATCHING "${escapeHtml(searchQuery)}"</td></tr>`;
        return;
    }

    const maxRows = searchQuery ? 20 : 10;
    list.slice(0, maxRows).forEach((artist, idx) => {
        const tr = document.createElement("tr");
        tr.innerHTML = `
            <td>
                <span class="rank-badge">#${idx + 1}</span>
                <strong style="margin-left: 8px;">${escapeHtml(artist.artist_name)}</strong>
            </td>
            <td><span style="font-family: var(--font-mono); font-weight: bold;">${artist.total_tracks} tracks</span></td>
            <td><span class="${activeSort === 'popularity' ? 'metric-highlight' : ''}">${artist.avg_popularity}</span></td>
            <td><span style="font-family: var(--font-mono); ${activeSort === 'duration' ? 'color: var(--color-orange); font-weight: bold;' : ''}">${artist.avg_duration_sec}s</span></td>
            <td><span style="font-family: var(--font-mono); font-weight: bold; ${activeSort === 'year' ? 'color: var(--color-orange);' : ''}">${artist.latest_year || 2023}</span></td>
        `;
        tbody.appendChild(tr);
    });
}

function renderTopTracksTable() {
    const tbody = document.querySelector("#top-tracks-table tbody");
    if (!tbody) return;
    tbody.innerHTML = "";

    let list = [];
    if (searchQuery) {
        if (liveSearchTracks && liveSearchTracks.length) {
            list = [...liveSearchTracks];
        } else {
            const q = searchQuery.toLowerCase();
            const source = (cachedCatalogIndex.popular_tracks && cachedCatalogIndex.popular_tracks.length)
                ? cachedCatalogIndex.popular_tracks
                : cachedTopTracks;
            list = source.filter(t => 
                t.track_name.toLowerCase().includes(q) || 
                t.artist_name.toLowerCase().includes(q) ||
                t.genre.toLowerCase().includes(q) ||
                (t.album_name && t.album_name.toLowerCase().includes(q))
            );
        }
    } else {
        list = [...cachedTopTracks];
    }

    // Genre filter
    if (activeGenreFilter !== "ALL") {
        list = list.filter(t => t.genre.toLowerCase() === activeGenreFilter.toLowerCase());
    }

    // Accurate Multi-Column Sorting
    if (activeSort === "popularity") {
        list.sort((a, b) => b.popularity - a.popularity);
    } else if (activeSort === "year") {
        list.sort((a, b) => b.year - a.year || b.popularity - a.popularity);
    } else if (activeSort === "volume") {
        list.sort((a, b) => (a.rank || 1) - (b.rank || 1));
    } else if (activeSort === "duration") {
        list.sort((a, b) => (b.duration_sec || 0) - (a.duration_sec || 0));
    }

    if (list.length === 0) {
        tbody.innerHTML = `<tr><td colspan="6" style="text-align:center; padding: 20px; font-family: var(--font-mono); font-weight: bold;">NO TRACKS FOUND MATCHING FILTER</td></tr>`;
        return;
    }

    const maxRows = searchQuery ? 25 : 12;
    list.slice(0, maxRows).forEach((track, idx) => {
        const tr = document.createElement("tr");
        tr.innerHTML = `
            <td><span class="genre-tag-cell">${escapeHtml(track.genre)}</span></td>
            <td><span class="rank-badge">#${track.rank || (idx + 1)}</span></td>
            <td><strong>${escapeHtml(track.track_name)}</strong></td>
            <td>${escapeHtml(track.artist_name)}</td>
            <td><span class="${activeSort === 'popularity' ? 'metric-highlight' : ''}">${track.popularity}</span></td>
            <td><span style="font-family: var(--font-mono); font-weight: bold; ${activeSort === 'year' ? 'color: var(--color-orange);' : ''}">${track.year}</span></td>
        `;
        tbody.appendChild(tr);
    });
}

/* ==========================================================================
   Hero Landing Boxes Smooth Redirection
   ========================================================================== */

function initHeroBoxRedirects() {
    const heroItems = document.querySelectorAll(".hero-item");
    heroItems.forEach(item => {
        item.addEventListener("click", (e) => {
            const href = item.getAttribute("href");

            // Card 6: Groq Ingestion Dialog
            if (item.id === "hero-cta-groq" || href === "#ingest-modal") {
                e.preventDefault();
                const modal = document.getElementById("ingest-modal");
                if (modal) {
                    modal.classList.remove("hidden");
                    document.body.classList.add("modal-open");
                    const input = document.getElementById("input-song-name");
                    if (input) input.focus();
                }
                return;
            }

            // Cards 1-5: Smooth Scroll to explicit section ID
            if (href && href.startsWith("#")) {
                e.preventDefault();
                const targetEl = document.querySelector(href);
                if (targetEl) {
                    targetEl.scrollIntoView({ behavior: "smooth", block: "start" });
                    targetEl.classList.add("highlight-target");
                    setTimeout(() => targetEl.classList.remove("highlight-target"), 1600);
                }
            }
        });
    });

    // Also support sidebar navigation pills
    const navPills = document.querySelectorAll(".nav-pill");
    navPills.forEach(pill => {
        pill.addEventListener("click", (e) => {
            const href = pill.getAttribute("href");
            if (href && href.startsWith("#")) {
                e.preventDefault();
                const targetEl = document.querySelector(href);
                if (targetEl) {
                    targetEl.scrollIntoView({ behavior: "smooth", block: "start" });
                    targetEl.classList.add("highlight-target");
                    setTimeout(() => targetEl.classList.remove("highlight-target"), 1600);
                }
            }
        });
    });
}

/* ==========================================================================
   Interactive Controls & Listeners
   ========================================================================== */

function initControls() {
    // 1. Live Search Inputs
    const mainSearch = document.getElementById("search-input");
    const sideSearch = document.getElementById("sidebar-search-input");

    function handleSearch(val) {
        searchQuery = val.trim();
        if (mainSearch && mainSearch.value !== val) mainSearch.value = val;
        if (sideSearch && sideSearch.value !== val) sideSearch.value = val;

        clearTimeout(searchDebounceTimer);
        if (!searchQuery) {
            liveSearchTracks = null;
            liveSearchArtists = null;
            applyFiltersAndRenderTables();
            return;
        }

        // Fast local client-side filter immediately for instant feedback
        applyFiltersAndRenderTables();

        // Then execute debounced API search against all 85k tracks in the lakehouse
        searchDebounceTimer = setTimeout(async () => {
            try {
                const res = await fetch(`/api/search?q=${encodeURIComponent(searchQuery)}&genre=${encodeURIComponent(activeGenreFilter)}&sort=${encodeURIComponent(activeSort)}&limit=50`);
                if (res.ok) {
                    const data = await res.json();
                    if (data.query === searchQuery) {
                        liveSearchTracks = data.tracks || [];
                        liveSearchArtists = data.artists || [];
                        applyFiltersAndRenderTables();
                    }
                }
            } catch (err) {
                console.warn("Live lakehouse search API error, using local index:", err);
            }
        }, 120);
    }

    if (mainSearch) mainSearch.addEventListener("input", (e) => handleSearch(e.target.value));
    if (sideSearch) sideSearch.addEventListener("input", (e) => handleSearch(e.target.value));

    // 2. Single Unified Sort Row
    const sortPills = document.querySelectorAll(".sort-pill:not(.sort-pill--datafeed)");
    sortPills.forEach(pill => {
        pill.addEventListener("click", () => {
            const sortKey = pill.dataset.sort;
            if (!sortKey) return;
            activeSort = sortKey;

            sortPills.forEach(p => {
                if (p.dataset.sort === sortKey) p.classList.add("active");
                else p.classList.remove("active");
            });

            applyFiltersAndRenderTables();
        });
    });

    // 3. Genre Filter Buttons
    const genreBtns = document.querySelectorAll(".genre-filter-btn");
    genreBtns.forEach(btn => {
        btn.addEventListener("click", () => {
            genreBtns.forEach(b => b.classList.remove("active"));
            btn.classList.add("active");
            activeGenreFilter = btn.dataset.genre || "ALL";
            applyFiltersAndRenderTables();
        });
    });

    // 4. Data Feed Toggle
    const toggleDatafeed = document.getElementById("btn-toggle-datafeed");
    const datafeedSection = document.getElementById("mini-dashboard-section");
    if (toggleDatafeed && datafeedSection) {
        toggleDatafeed.addEventListener("click", () => {
            if (datafeedSection.style.display === "none") {
                datafeedSection.style.display = "block";
                toggleDatafeed.classList.add("active");
            } else {
                datafeedSection.style.display = "none";
                toggleDatafeed.classList.remove("active");
            }
        });
    }

    // 5. Trigger Full Pipeline from Banner
    const btnTriggerPipeline = document.getElementById("btn-trigger-full-pipeline");
    if (btnTriggerPipeline) {
        btnTriggerPipeline.addEventListener("click", async () => {
            const modal = document.getElementById("ingest-modal");
            const consoleContainer = document.getElementById("execution-console-container");
            const finishBanner = document.getElementById("console-finish-msg");

            if (modal) {
                modal.classList.remove("hidden");
                document.body.classList.add("modal-open");
            }
            if (consoleContainer) consoleContainer.classList.remove("hidden");
            if (finishBanner) finishBanner.classList.add("hidden");

            try {
                const res = await fetch("/api/pipeline/run", { method: "POST" });
                const data = await res.json();
                if (data.success) {
                    startPipelinePolling();
                } else {
                    alert(data.message || "Failed to trigger pipeline");
                }
            } catch (err) {
                alert("Trigger Error: " + err.message);
            }
        });
    }
}

/* ==========================================================================
   Ingestion Modal & Groq Metadata Client
   ========================================================================== */

function initIngestionModal() {
    const modal = document.getElementById("ingest-modal");
    const btnClose = document.getElementById("btn-close-modal");
    const btnLookup = document.getElementById("btn-lookup-song");
    const btnConfirm = document.getElementById("btn-confirm-ingest");

    if (btnClose) {
        btnClose.addEventListener("click", () => {
            modal.classList.add("hidden");
            document.body.classList.remove("modal-open");
        });
    }

    if (modal) {
        modal.addEventListener("click", (e) => {
            if (e.target === modal) {
                modal.classList.add("hidden");
                document.body.classList.remove("modal-open");
            }
        });
    }

    if (btnLookup) btnLookup.addEventListener("click", handleLookupSong);
    if (btnConfirm) btnConfirm.addEventListener("click", handleConfirmIngest);
}

async function handleLookupSong() {
    const songName = document.getElementById("input-song-name").value.trim();
    const artistHint = document.getElementById("input-artist-hint").value.trim();
    const apiKey = document.getElementById("input-groq-key").value.trim();

    const errBox = document.getElementById("lookup-error-msg");
    const previewContainer = document.getElementById("preview-container");
    const spinner = document.getElementById("lookup-spinner");
    const btnText = document.getElementById("lookup-btn-text");

    errBox.classList.add("hidden");
    previewContainer.classList.add("hidden");

    const inputSongEl = document.getElementById("input-song-name");
    const formGroupEl = inputSongEl.closest(".form-group");

    if (!songName) {
        if (formGroupEl) {
            formGroupEl.classList.add("has-error");
            inputSongEl.focus();
            inputSongEl.addEventListener("input", () => {
                formGroupEl.classList.remove("has-error");
            }, { once: true });
        }
        errBox.textContent = "⚠️ Please enter a song title.";
        errBox.classList.remove("hidden");
        return;
    } else {
        if (formGroupEl) formGroupEl.classList.remove("has-error");
    }

    spinner.classList.remove("hidden");
    btnText.textContent = "Extracting Metadata with Groq...";
    document.getElementById("btn-lookup-song").disabled = true;

    try {
        const res = await fetch("/api/song/lookup", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                song_name: songName,
                artist: artistHint,
                api_key: apiKey
            })
        });

        const data = await res.json();
        if (!res.ok || !data.success) {
            throw new Error(data.error || "Failed to extract metadata.");
        }

        currentExtractedMetadata = data.metadata;
        currentExtractedMetadata._already_in_db = !!data.already_in_database;
        renderMetadataPreview(data.metadata, data.already_in_database, data.source);
        previewContainer.classList.remove("hidden");
    } catch (err) {
        errBox.innerHTML = `⚠️ <span>${escapeHtml(err.message)}</span>`;
        errBox.classList.remove("hidden");
    } finally {
        spinner.classList.add("hidden");
        btnText.textContent = "🔍 Extract Metadata with Groq";
        document.getElementById("btn-lookup-song").disabled = false;
    }
}

function renderMetadataPreview(meta, isAlreadyInDb, source) {
    const previewHeader = document.querySelector(".preview-header");
    const btnConfirm = document.getElementById("btn-confirm-ingest");

    const RECOGNIZED_GENRES = [
        "Pop", "Hip-Hop", "Indie", "Rock", "R&B",
        "Classical", "Jazz", "Electronic", "Country", "Metal"
    ];

    if (isAlreadyInDb) {
        previewHeader.innerHTML = `
            <div>
                <h3>Catalog Record Retrieved from Database</h3>
                <div style="font-family: var(--font-mono); font-size: 11px; opacity: 0.8; margin-top: 4px;">✏️ Review or edit any field below before re-running.</div>
            </div>
            <span class="badge-database">📦 Found in Existing Catalog (Database)</span>
        `;
        btnConfirm.textContent = "🔄 Re-Run Pipeline on Catalog";
    } else {
        const badgeLabel = (meta.source === "verified_catalog" || meta.candidates) 
            ? "🎵 Verified Global Catalog" 
            : "✨ Extracted via Groq AI";
        previewHeader.innerHTML = `
            <div>
                <h3>Extracted Catalog Metadata (Human-in-the-Loop Review)</h3>
                <div style="font-family: var(--font-mono); font-size: 11px; opacity: 0.8; margin-top: 4px;">✏️ Verified catalog metadata loaded below. You can switch releases or edit any field before ingesting!</div>
            </div>
            <span class="badge-valid">${badgeLabel}</span>
        `;
        btnConfirm.textContent = "🚀 Ingest into HDFS & Run Pipeline";
    }

    const candidatesBox = document.getElementById("candidates-box");
    if (meta.candidates && meta.candidates.length > 1) {
        candidatesBox.innerHTML = `
            <div class="candidates-bar">
                <div class="candidates-title">💡 Multiple Soundtracks / Releases Found (Click to Switch):</div>
                <div class="candidates-list">
                    ${meta.candidates.map((c, idx) => `
                        <button type="button" class="candidate-btn ${idx === 0 ? 'active' : ''}" data-idx="${idx}">
                            🎵 ${escapeHtml(c.label)}
                        </button>
                    `).join('')}
                </div>
            </div>
        `;

        const candBtns = candidatesBox.querySelectorAll(".candidate-btn");
        candBtns.forEach(btn => {
            btn.addEventListener("click", () => {
                const idx = parseInt(btn.dataset.idx, 10);
                const cand = meta.candidates[idx].metadata;
                if (!cand) return;
                candBtns.forEach(b => b.classList.remove("active"));
                btn.classList.add("active");

                document.getElementById("edit-track-name").value = cand.track_name || "";
                document.getElementById("edit-artist-name").value = cand.artist_name || "";
                document.getElementById("edit-album-name").value = cand.album_name || "";
                document.getElementById("edit-year").value = cand.year || 2022;
                document.getElementById("edit-duration-sec").value = Math.round((cand.duration_ms || 215000) / 1000);
                if (cand.genre) document.getElementById("edit-genre").value = cand.genre;
                if (cand.track_id) document.getElementById("edit-track-id").value = cand.track_id;
                if (cand.explicit !== undefined) document.getElementById("edit-explicit").value = cand.explicit;
                if (cand.popularity !== undefined) document.getElementById("edit-popularity").value = cand.popularity;
            });
        });
    } else if (candidatesBox) {
        candidatesBox.innerHTML = "";
    }

    const grid = document.getElementById("metadata-grid");
    grid.innerHTML = `
        <div class="meta-field">
            <label class="meta-field-label" for="edit-track-name">Track Title *</label>
            <input type="text" id="edit-track-name" class="meta-edit-input" value="${escapeHtml(meta.track_name)}">
        </div>
        <div class="meta-field">
            <label class="meta-field-label" for="edit-artist-name">Artist / Composer *</label>
            <input type="text" id="edit-artist-name" class="meta-edit-input" value="${escapeHtml(meta.artist_name)}">
        </div>
        <div class="meta-field">
            <label class="meta-field-label" for="edit-genre">Genre *</label>
            <select id="edit-genre" class="meta-edit-select">
                ${RECOGNIZED_GENRES.map(g => `<option value="${g}" ${g.toLowerCase() === (meta.genre || '').toLowerCase() ? 'selected' : ''}>${g}</option>`).join('')}
            </select>
        </div>
        <div class="meta-field">
            <label class="meta-field-label" for="edit-album-name">Album / Movie Title</label>
            <input type="text" id="edit-album-name" class="meta-edit-input" value="${escapeHtml(meta.album_name || '')}">
        </div>
        <div class="meta-field">
            <label class="meta-field-label" for="edit-popularity">Popularity (0-100)</label>
            <input type="number" id="edit-popularity" class="meta-edit-input" min="0" max="100" value="${meta.popularity}">
        </div>
        <div class="meta-field">
            <label class="meta-field-label" for="edit-duration-sec">Duration (Seconds)</label>
            <input type="number" id="edit-duration-sec" class="meta-edit-input" min="1" max="3600" value="${Math.round(meta.duration_ms / 1000)}">
        </div>
        <div class="meta-field">
            <label class="meta-field-label" for="edit-year">Year (1950-2026)</label>
            <input type="number" id="edit-year" class="meta-edit-input" min="1950" max="2026" value="${meta.year}">
        </div>
        <div class="meta-field">
            <label class="meta-field-label" for="edit-explicit">Advisory</label>
            <select id="edit-explicit" class="meta-edit-select">
                <option value="0" ${meta.explicit == 0 ? 'selected' : ''}>Clean (0)</option>
                <option value="1" ${meta.explicit == 1 ? 'selected' : ''}>Explicit (1)</option>
            </select>
        </div>
        <div class="meta-field">
            <label class="meta-field-label" for="edit-track-id">Track ID</label>
            <input type="text" id="edit-track-id" class="meta-edit-input" value="${escapeHtml(meta.track_id)}">
        </div>
    `;
}

async function handleConfirmIngest() {
    if (!currentExtractedMetadata) return;

    const trackName = document.getElementById("edit-track-name").value.trim();
    const artistName = document.getElementById("edit-artist-name").value.trim();
    if (!trackName || !artistName) {
        alert("Track Title and Artist Name cannot be blank.");
        return;
    }

    const durationSec = parseInt(document.getElementById("edit-duration-sec").value, 10) || 210;
    const finalPayload = {
        track_id: document.getElementById("edit-track-id").value.trim() || currentExtractedMetadata.track_id,
        track_name: trackName,
        artist_name: artistName,
        album_name: document.getElementById("edit-album-name").value.trim() || "Unknown Album",
        genre: document.getElementById("edit-genre").value,
        popularity: Math.max(0, Math.min(100, parseInt(document.getElementById("edit-popularity").value, 10) || 50)),
        duration_ms: Math.max(1000, durationSec * 1000),
        explicit: parseInt(document.getElementById("edit-explicit").value, 10) || 0,
        year: Math.max(1950, Math.min(2026, parseInt(document.getElementById("edit-year").value, 10) || 2020))
    };

    const runPipeline = document.getElementById("check-run-pipeline").checked;
    const btnConfirm = document.getElementById("btn-confirm-ingest");
    const consoleContainer = document.getElementById("execution-console-container");
    const finishBanner = document.getElementById("console-finish-msg");

    btnConfirm.disabled = true;
    finishBanner.classList.add("hidden");
    consoleContainer.classList.remove("hidden");

    try {
        const res = await fetch("/api/song/ingest", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                metadata: finalPayload,
                run_pipeline: runPipeline,
                already_in_database: currentExtractedMetadata._already_in_db || false
            })
        });

        const data = await res.json();
        if (!res.ok || !data.success) {
            throw new Error(data.error || "Ingestion request failed.");
        }

        if (runPipeline) {
            startPipelinePolling();
        } else {
            finishBanner.textContent = "Track appended to dataset. Pipeline execution deferred.";
            finishBanner.classList.remove("hidden");
            btnConfirm.disabled = false;
        }
    } catch (err) {
        alert("Ingestion Error: " + err.message);
        btnConfirm.disabled = false;
    }
}

function startPipelinePolling() {
    if (pipelinePollInterval) clearInterval(pipelinePollInterval);

    const stageText = document.getElementById("console-stage-text");
    const timerText = document.getElementById("console-timer");
    const logBox = document.getElementById("console-log-box");
    const finishBanner = document.getElementById("console-finish-msg");
    const btnConfirm = document.getElementById("btn-confirm-ingest");

    pipelinePollInterval = setInterval(async () => {
        try {
            const res = await fetch("/api/pipeline/status");
            const state = await res.json();

            stageText.textContent = state.current_stage || "Processing...";
            timerText.textContent = `${state.elapsed_seconds || 0}s`;

            // Stream logs
            logBox.innerHTML = "";
            (state.recent_logs || []).forEach(log => {
                const p = document.createElement("div");
                p.textContent = log;
                logBox.appendChild(p);
            });
            logBox.scrollTop = logBox.scrollHeight;

            if (!state.running) {
                clearInterval(pipelinePollInterval);
                pipelinePollInterval = null;
                btnConfirm.disabled = false;

                if (state.status === "SUCCESS" || state.status === "READY") {
                    finishBanner.classList.remove("hidden");
                    finishBanner.textContent = "🎉 Ingestion and Lakehouse analytics verified! Dashboard telemetry synced.";
                    finishBanner.style.background = "#DCFCE7";
                    finishBanner.style.color = "#15803D";
                    await loadDashboardData();
                } else {
                    finishBanner.textContent = "Pipeline execution failed. Check console output.";
                    finishBanner.classList.remove("hidden");
                    finishBanner.style.background = "#FEE2E2";
                    finishBanner.style.color = "#B91C1C";
                }
            }
        } catch (err) {
            console.error("Polling error:", err);
        }
    }, 1200);
}

async function checkInitialPipelineStatus() {
    try {
        const res = await fetch("/api/pipeline/status");
        const state = await res.json();
        if (state.running) {
            startPipelinePolling();
        }
    } catch (_) {}
}

function escapeHtml(str) {
    if (!str) return "";
    return str.replace(/[&<>'"]/g, 
        tag => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', "'": '&#39;', '"': '&quot;' }[tag] || tag)
    );
}

function initHeroFoldCTA() {
    const btnHeroCta = document.getElementById("btn-hero-cta-ingest");
    if (btnHeroCta) {
        btnHeroCta.addEventListener("click", () => {
            const modal = document.getElementById("ingest-modal");
            if (modal) {
                modal.classList.remove("hidden");
                document.body.classList.add("modal-open");
                const input = document.getElementById("input-song-name");
                if (input) input.focus();
                if (window.trackEvent) trackEvent("cta_click", { action: "open_groq_modal_from_hero" });
            }
        });
    }
}

function initCookieBanner() {
    const banner = document.getElementById("cookie-banner");
    const btnAccept = document.getElementById("btn-cookie-accept");
    const btnDecline = document.getElementById("btn-cookie-decline");
    if (!banner || !btnAccept || !btnDecline) return;

    const consent = localStorage.getItem("beatdrop_cookie_consent");
    if (!consent) {
        banner.classList.remove("hidden");
    }

    btnAccept.addEventListener("click", () => {
        localStorage.setItem("beatdrop_cookie_consent", "accepted");
        banner.classList.add("hidden");
        if (window.trackEvent) trackEvent("cookie_consent", { choice: "accepted" });
    });

    btnDecline.addEventListener("click", () => {
        localStorage.setItem("beatdrop_cookie_consent", "declined");
        banner.classList.add("hidden");
        if (window.trackEvent) trackEvent("cookie_consent", { choice: "declined" });
    });
}

/* Catalog Track Spotlight & Randomizer */
const SPOTLIGHT_TRACKS = [
    { title: "Bohemian Rhapsody", artist: "Queen", genre: "Rock", year: 1975, pop: 98 },
    { title: "Starboy", artist: "The Weeknd", genre: "R&B", year: 2016, pop: 96 },
    { title: "Hotel California", artist: "Eagles", genre: "Rock", year: 1976, pop: 95 },
    { title: "Ala Boleto", artist: "Anirudh Ravichander", genre: "Pop", year: 2026, pop: 97 },
    { title: "Billie Jean", artist: "Michael Jackson", genre: "Pop", year: 1982, pop: 97 },
    { title: "In the End", artist: "Linkin Park", genre: "Metal", year: 2000, pop: 94 },
    { title: "Lose Yourself", artist: "Eminem", genre: "Hip-Hop", year: 2002, pop: 96 },
    { title: "Money Trees", artist: "Kendrick Lamar", genre: "Hip-Hop", year: 2012, pop: 100 },
    { title: "The Less I Know the Better", artist: "Tame Impala", genre: "Indie", year: 2015, pop: 100 },
    { title: "Get Lucky", artist: "Daft Punk", genre: "Electronic", year: 2013, pop: 92 },
    { title: "Take Five", artist: "Dave Brubeck", genre: "Jazz", year: 1959, pop: 89 },
    { title: "Jolene", artist: "Dolly Parton", genre: "Country", year: 1973, pop: 91 }
];

let spotlightIndex = 0;

function updateSpotlightUI(track) {
    const elTitle = document.getElementById("spotlight-title");
    const elArtist = document.getElementById("spotlight-artist");
    const elGenre = document.getElementById("spotlight-genre");
    const elYear = document.getElementById("spotlight-year");
    const elPop = document.getElementById("spotlight-pop");

    if (elTitle) elTitle.textContent = track.title;
    if (elArtist) elArtist.textContent = track.artist;
    if (elGenre) elGenre.textContent = track.genre;
    if (elYear) elYear.textContent = track.year;
    if (elPop) elPop.textContent = `🔥 ${track.pop} POP`;
}

function initTrackSpotlight() {
    const btnNext = document.getElementById("btn-spotlight-next");
    const btnFilter = document.getElementById("btn-spotlight-filter");
    if (!btnNext || !btnFilter) return;

    btnNext.addEventListener("click", () => {
        spotlightIndex = (spotlightIndex + 1) % SPOTLIGHT_TRACKS.length;
        const track = SPOTLIGHT_TRACKS[spotlightIndex];
        updateSpotlightUI(track);
        if (window.trackEvent) trackEvent("spotlight_roll", { track: track.title, artist: track.artist });
    });

    btnFilter.addEventListener("click", () => {
        const track = SPOTLIGHT_TRACKS[spotlightIndex];
        const searchInput = document.getElementById("search-input");
        const sidebarSearchInput = document.getElementById("sidebar-search-input");
        if (searchInput) searchInput.value = track.artist;
        if (sidebarSearchInput) sidebarSearchInput.value = track.artist;
        searchQuery = track.artist.toLowerCase();
        renderTopArtistsTable();
        renderTopTracksTable();

        const target = document.getElementById("section-top-artists");
        if (target) {
            target.scrollIntoView({ behavior: "smooth", block: "start" });
            target.classList.add("highlight-target");
            setTimeout(() => target.classList.remove("highlight-target"), 1600);
        }
        if (window.trackEvent) trackEvent("spotlight_filter_artist", { artist: track.artist });
    });
}


