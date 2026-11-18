// The site's viewer-request function (Phase 6.5 IMPLEMENTATION doc, decision B; section 7 item 2). Runtime
// cloudfront-js-2.0. Every page of the explorer is a file at <path>/index.html, and the bucket is private, so S3
// cannot pick an index document itself:
//   - a path ending in "/" is served its own index.html (so /methods/ serves methods/index.html, its own title
//     and share card, to a reader running no script);
//   - a path whose last segment has no file extension ("/methods") is redirected, permanently, to the same path
//     with "/" added, its query string kept; the Location is relative, so it stays on whichever host was asked
//     (the public address's rewrite or the distribution's own);
//   - anything else (a file: /assets/x.js, /data/index.json, /404.html) passes unchanged.
// A path that names no file then fails at the bucket, and the distribution answers with /404.html and status 404.
// web/scripts/site-paths.test.ts runs this file's handler on each case.
function handler(event) {
  var request = event.request;
  var uri = request.uri;
  if (uri.charAt(uri.length - 1) === "/") {
    request.uri = uri + "index.html";
    return request;
  }
  var last = uri.substring(uri.lastIndexOf("/") + 1);
  if (last.indexOf(".") !== -1) return request;
  var query = [];
  var params = request.querystring || {};
  for (var key in params) {
    var param = params[key];
    if (param.multiValue) {
      for (var i = 0; i < param.multiValue.length; i++) query.push(key + "=" + param.multiValue[i].value);
    } else {
      query.push(key + "=" + param.value);
    }
  }
  return {
    statusCode: 301,
    statusDescription: "Moved Permanently",
    headers: { location: { value: uri + "/" + (query.length > 0 ? "?" + query.join("&") : "") } },
  };
}
