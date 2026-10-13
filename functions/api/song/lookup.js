export async function onRequestOptions() {
  return new Response(null, {
    status: 204,
    headers: {
      "Access-Control-Allow-Origin": "*",
      "Access-Control-Allow-Methods": "POST, OPTIONS",
      "Access-Control-Allow-Headers": "Content-Type"
    }
  });
}

export async function onRequestPost(context) {
  try {
    let body = {};
    try {
      body = await context.request.json();
    } catch (e) {
      body = {};
    }

    const songName = (body.song_name || "").trim();
    const artistHint = (body.artist || body.artist_hint || "").trim();
    const apiKey = (body.api_key || body.groq_key || "").trim() || context.env?.GROQ_API_KEY || "";

    if (!songName) {
      return new Response(JSON.stringify({ success: false, error: "Song name is required." }), {
        status: 400,
        headers: {
          "Content-Type": "application/json",
          "Access-Control-Allow-Origin": "*"
        }
      });
    }

    if (!apiKey) {
      // Mock / fallback metadata when no key is supplied
      return new Response(JSON.stringify({
        success: true,
        source: "cloudflare_mock",
        is_valid: true,
        metadata: {
          track_name: songName,
          artist_name: artistHint || "Featured Artist",
          album_name: `${songName} - Single`,
          genre: "Pop",
          popularity: 88,
          duration_ms: 215000,
          explicit: 0,
          year: 2024
        }
      }), {
        headers: {
          "Content-Type": "application/json",
          "Access-Control-Allow-Origin": "*"
        }
      });
    }

    // Call Groq API from Cloudflare Edge
    const prompt = `You are a music metadata engine. Extract metadata for the song: "${songName}" ${artistHint ? `by artist "${artistHint}"` : ""}.
Return ONLY valid JSON matching this exact structure:
{
  "track_name": "exact official title",
  "artist_name": "canonical artist",
  "album_name": "album or single name",
  "genre": "one of: Pop, Hip-Hop, Indie, Rock, R&B, Classical, Jazz, Electronic, Country, Metal",
  "popularity": integer between 0 and 100,
  "duration_ms": integer track duration in milliseconds,
  "explicit": 0 or 1,
  "year": integer 4-digit release year
}`;

    const groqRes = await fetch("https://api.groq.com/openai/v1/chat/completions", {
      method: "POST",
      headers: {
        "Authorization": `Bearer ${apiKey}`,
        "Content-Type": "application/json"
      },
      body: JSON.stringify({
        model: "llama-3.3-70b-versatile",
        messages: [{ role: "user", content: prompt }],
        temperature: 0.1,
        response_format: { type: "json_object" }
      })
    });

    if (!groqRes.ok) {
      const errText = await groqRes.text();
      throw new Error(`Groq API returned ${groqRes.status}: ${errText}`);
    }

    const groqData = await groqRes.json();
    const content = groqData.choices?.[0]?.message?.content || "{}";
    const meta = JSON.parse(content);

    return new Response(JSON.stringify({
      success: true,
      source: "groq_api_cloudflare",
      is_valid: true,
      metadata: {
        track_name: meta.track_name || songName,
        artist_name: meta.artist_name || artistHint || "Unknown Artist",
        album_name: meta.album_name || `${songName} - Single`,
        genre: meta.genre || "Pop",
        popularity: Number(meta.popularity) || 75,
        duration_ms: Number(meta.duration_ms) || 210000,
        explicit: meta.explicit ? 1 : 0,
        year: Number(meta.year) || 2024
      }
    }), {
      headers: {
        "Content-Type": "application/json",
        "Access-Control-Allow-Origin": "*"
      }
    });

  } catch (err) {
    return new Response(JSON.stringify({ success: false, error: err.message }), {
      status: 500,
      headers: {
        "Content-Type": "application/json",
        "Access-Control-Allow-Origin": "*"
      }
    });
  }
}
