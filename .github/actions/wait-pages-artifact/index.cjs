'use strict';
const {DefaultArtifactClient} = require('@actions/artifact');
const {waitForArtifact} = require('./wait.cjs');
// An action receives the job-scoped runtime token automatically. Never log it.
const name = process.env['INPUT_ARTIFACT-NAME'];
const id = process.env['INPUT_ARTIFACT-ID'];
if (name !== `github-pages-${process.env.GITHUB_RUN_ID}-${process.env.GITHUB_RUN_ATTEMPT}`) {
  console.error('::error::Pages artifact must belong to this run and attempt');
  process.exit(1);
}
const hardLimit = setTimeout(() => {
  console.error('::error::Artifact readiness exceeded 90 seconds; deployment not started');
  process.exit(1);
}, 90000);
const client = new DefaultArtifactClient();
waitForArtifact({list: () => client.listArtifacts(), name, id}).then(() => {
  clearTimeout(hardLimit);
}).catch(error => {
  clearTimeout(hardLimit);
  // Do not expose service responses, runtime credentials or request headers.
  const safe = /^(Invalid expected|Invalid artifact|Multiple matching|Pages artifact|Invalid Pages)/.test(error.message);
  console.error('::error::' + (safe ? error.message : 'Artifact service check failed; deployment not started'));
  process.exit(1);
});
