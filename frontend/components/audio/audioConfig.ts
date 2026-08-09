export interface AudioTrack {
  key: string;
  label: string;
  url: string;
}

export const AUDIO_TRACKS: AudioTrack[] = [
  {
    key: "track1.mp3",
    label: "Ambient 1",
    url: process.env.NEXT_PUBLIC_R2_PUBLIC_URL
      ? `${process.env.NEXT_PUBLIC_R2_PUBLIC_URL}/audio/track1.mp3`
      : "/audio/track1.mp3",
  },
  {
    key: "track2.mp3",
    label: "Ambient 2",
    url: process.env.NEXT_PUBLIC_R2_PUBLIC_URL
      ? `${process.env.NEXT_PUBLIC_R2_PUBLIC_URL}/audio/track2.mp3`
      : "/audio/track2.mp3",
  },
];
