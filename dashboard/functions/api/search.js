/**
 * Cloudflare Pages Function — /api/search
 * Client-side search endpoint that loads the catalog index JSON
 * and performs filtering, sorting, and pagination on the edge.
 */

export async function onRequestGet(context) {
  const url = new URL(context.request.url);
  const q = (url.searchParams.get("q") || "").trim().toLowerCase();
  const genre = (url.searchParams.get("genre") || "ALL").trim().toUpperCase();
  const sortBy = url.searchParams.get("sort") || "popularity";
  const limit = Math.min(parseInt(url.searchParams.get("limit") || "50", 10), 200);

  try {
    // Fetch the pre-built catalog search index (served as a static asset)
    const origin = url.origin;
    const indexRes = await fetch(`${origin}/data/catalog_search_index.json`);
    if (!indexRes.ok) {
      throw new Error(`Failed to load catalog index: ${indexRes.status}`);
    }
    const catalog = await indexRes.json();
    const allTracks = catalog.popular_tracks || [];
    const allArtists = catalog.top_artists || [];

    // Filter tracks
    let matchingTracks = allTracks.filter(t => {
      // Genre filter
      if (genre !== "ALL" && (t.genre || "").toUpperCase() !== genre) return false;
      // Query match
      if (!q) return true;
      const searchStr = `${(t.track_name || "").toLowerCase()} ${(t.artist_name || "").toLowerCase()} ${(t.album_name || "").toLowerCase()} ${(t.genre || "").toLowerCase()}`;
      return searchStr.includes(q);
    });

    // Filter artists
    let matchingArtists = allArtists.filter(a => {
      if (!q) return true;
      return (a.artist_name || "").toLowerCase().includes(q);
    });

    // Sort tracks
    if (sortBy === "popularity") {
      matchingTracks.sort((a, b) => (b.popularity || 0) - (a.popularity || 0));
      matchingArtists.sort((a, b) => (b.avg_popularity || 0) - (a.avg_popularity || 0));
    } else if (sortBy === "year") {
      matchingTracks.sort((a, b) => (b.year || 0) - (a.year || 0));
      matchingArtists.sort((a, b) => (b.latest_year || 0) - (a.latest_year || 0));
    } else if (sortBy === "duration") {
      matchingTracks.sort((a, b) => (b.duration_sec || 0) - (a.duration_sec || 0));
      matchingArtists.sort((a, b) => (b.avg_duration_sec || 0) - (a.avg_duration_sec || 0));
    } else if (sortBy === "volume") {
      matchingArtists.sort((a, b) => (b.total_tracks || 0) - (a.total_tracks || 0));
    }

    return new Response(JSON.stringify({
      query: url.searchParams.get("q") || "",
      genre: url.searchParams.get("genre") || "ALL",
      sort_by: sortBy,
      total_track_matches: matchingTracks.length,
      total_artist_matches: matchingArtists.length,
      tracks: matchingTracks.slice(0, limit),
      artists: matchingArtists.slice(0, limit)
    }), {
      headers: {
        "Content-Type": "application/json",
        "Access-Control-Allow-Origin": "*",
        "Cache-Control": "public, max-age=60"
      }
    });

  } catch (err) {
    return new Response(JSON.stringify({
      query: url.searchParams.get("q") || "",
      genre: "ALL",
      sort_by: sortBy,
      total_track_matches: 0,
      total_artist_matches: 0,
      tracks: [],
      artists: [],
      error: err.message
    }), {
      status: 500,
      headers: {
        "Content-Type": "application/json",
        "Access-Control-Allow-Origin": "*"
      }
    });
  }
}
