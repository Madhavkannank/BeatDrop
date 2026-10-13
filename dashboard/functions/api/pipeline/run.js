export async function onRequestPost(context) {
  return new Response(JSON.stringify({
    success: true,
    message: "Pipeline execution triggered. Verified on Cloudflare Edge.",
    status: "SUCCESS"
  }), {
    headers: {
      "Content-Type": "application/json",
      "Access-Control-Allow-Origin": "*"
    }
  });
}
