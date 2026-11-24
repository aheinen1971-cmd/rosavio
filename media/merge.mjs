import {Input, BlobSource, MPEG_TS, MP4, Output, Mp4OutputFormat, BufferTarget,
  EncodedPacketSink, EncodedVideoPacketSource, EncodedAudioPacketSource} from './vendor/mediabunny.mjs';

export async function mergeTracks(video, audio, signal) {
  const input = blob => new Input({formats:[MPEG_TS, MP4], source:new BlobSource(blob)});
  const picture = input(video), sound = input(audio);
  const output = new Output({format:new Mp4OutputFormat(), target:new BufferTarget()});
  async function copy(track, dest, start) {
    let metadata = {decoderConfig:await track.getDecoderConfig()};
    for await (const packet of new EncodedPacketSink(track).packets()) {
      signal.throwIfAborted();
      await dest.add(packet.clone({timestamp:packet.timestamp-start}), metadata);
      metadata = undefined;
    }
    dest.close();
  }
  try {
    const v = await picture.getPrimaryVideoTrack(), a = await sound.getPrimaryAudioTrack();
    if (!v || !a) throw Error('In den ausgewählten Dateien fehlt die Bild- oder Tonspur.');
    const starts = await Promise.all([v.getFirstTimestampOrNull(), a.getFirstTimestampOrNull()]);
    if (starts.includes(null)) throw Error('Eine der beiden Spuren ist leer.');
    const start = Math.min(...starts);
    const vs = new EncodedVideoPacketSource(await v.getCodec());
    const as = new EncodedAudioPacketSource(await a.getCodec());
    output.addVideoTrack(vs);
    output.addAudioTrack(as);
    await output.start();
    await Promise.all([copy(v,vs,start), copy(a,as,start)]);
    signal.throwIfAborted();
    await output.finalize();
    return {blob:new Blob([output.target.buffer],{type:'video/mp4'}), ext:'mp4'};
  } finally {
    if (output.state === 'started') await output.cancel();
    picture.dispose();
    sound.dispose();
  }
}
