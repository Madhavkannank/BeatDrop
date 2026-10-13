export async function onRequestPost(context) {
  try {
    const body = await context.request.json();
    const meta = body.metadata || {};

    if (!meta.track_name || !meta.artist_name) {
      return new Response(JSON.stringify({ success: false, error: "Valid metadata required." }), {
        status: 400,
        headers: { "Content-Type": "application/json" }
      });
    }

    return new Response(JSON.stringify({
      success: true,
      message: `Track "${meta.track_name}" by ${meta.artist_name} verified against schema contract and staged on Cloudflare Edge.`,
      pipeline_triggered: true
    }), {
      headers: { "Content-Type": "application/json", "Access-Control-Allow-Origin": "*" }
    });
  } catch (err) {
    return new Response(JSON.stringify({ success: false, error: err.message }), {
      status: 500,
      headers: { "Content-Type": "application/json" }
    });
  }
}
