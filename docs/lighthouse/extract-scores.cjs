const fs = require("fs");
const path = require("path");

const dir = path.join(__dirname);
const names = [
  "healthcore-home-before",
  "healthcore-home-after",
  "backoffice-login-after",
];

function summarize(name) {
  const j = JSON.parse(fs.readFileSync(path.join(dir, `${name}.json`), "utf8"));
  const rec = {
    file: name,
    url: j.finalUrl || j.requestedUrl,
    score: Math.round(j.categories.performance.score * 100),
    lcp: j.audits["largest-contentful-paint"]?.displayValue || null,
    fcp: j.audits["first-contentful-paint"]?.displayValue || null,
    cls: j.audits["cumulative-layout-shift"]?.displayValue || null,
    tbt: j.audits["total-blocking-time"]?.displayValue || null,
    fetchTime: j.fetchTime,
    lighthouseVersion: j.lighthouseVersion,
  };
  const data = j.audits["final-screenshot"]?.details?.data;
  if (data) {
    const b64 = data.replace(/^data:image\/png;base64,/, "");
    fs.writeFileSync(path.join(dir, `${name}.png`), Buffer.from(b64, "base64"));
  }
  console.log(JSON.stringify(rec));
  return rec;
}

const rows = names.map(summarize);
fs.writeFileSync(
  path.join(dir, "scores.json"),
  `${JSON.stringify(
    {
      preset: "desktop",
      tool: "Lighthouse CLI",
      runtime: "next dev in Docker",
      rows,
    },
    null,
    2,
  )}\n`,
);
