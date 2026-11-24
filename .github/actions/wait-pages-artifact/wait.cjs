'use strict';
async function waitForArtifact({list, name, id, now = () => performance.now(),
  sleep = ms => new Promise(resolve => setTimeout(resolve, ms)), log = console.log,
  timeout = 90000, interval = 5000}) {
  if (!/^github-pages-\d+-\d+$/.test(name) || !/^[1-9]\d*$/.test(String(id)))
    throw new Error('Invalid expected Pages artifact identity');
  const deadline = now() + timeout;
  let attempts = 0;
  while (now() < deadline) {
    attempts++;
    const result = await list();
    if (!Array.isArray(result?.artifacts)) throw new Error('Invalid artifact listing');
    const matches = result.artifacts.filter(a => a.name === name);
    if (matches.length > 1) throw new Error('Multiple matching Pages artifacts');
    if (matches.length === 1) {
      const artifact = matches[0];
      if (String(artifact.id) !== String(id)) throw new Error('Pages artifact ID differs from upload');
      if (!Number.isFinite(artifact.size) || artifact.size <= 0) throw new Error('Invalid Pages artifact size');
      if (now() >= deadline) break;
      log(`Pages artifact ${id} is visible after ${attempts} check(s).`);
      return artifact;
    }
    const remaining = deadline - now();
    if (remaining <= 0) break;
    log(`Pages artifact not visible yet; bounded metadata check ${attempts}.`);
    await sleep(Math.min(interval, remaining));
  }
  throw new Error('Pages artifact did not become visible within 90 seconds; deployment not started');
}
module.exports = {waitForArtifact};
