function formatDuration(seconds) {
  const value = Math.round(seconds);
  const pad = n => String(n).padStart(2,'0');
  const minutes = Math.floor(value/60);
  return minutes >= 60 ? Math.floor(minutes/60)+':'+pad(minutes%60)+':'+pad(value%60) : minutes+':'+pad(value%60);
}
