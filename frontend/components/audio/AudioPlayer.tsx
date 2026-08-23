"use client";

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useRef,
  useState,
  type ReactNode,
} from "react";
import { AUDIO_TRACKS } from "./audioConfig";
import type { AudioTrack } from "./audioConfig";

const STORAGE_KEY = "audio-state";

interface AudioState {
  trackIndex: number;
  volume: number;
  playing: boolean;
}

function loadState(): AudioState {
  if (typeof window === "undefined")
    return { trackIndex: 0, volume: 0.5, playing: false };
  try {
    const raw = sessionStorage.getItem(STORAGE_KEY);
    if (raw) return JSON.parse(raw);
  } catch {
    // ignore
  }
  return { trackIndex: 0, volume: 0.5, playing: false };
}

function saveState(s: AudioState) {
  if (typeof window === "undefined") return;
  sessionStorage.setItem(STORAGE_KEY, JSON.stringify(s));
}

interface AudioControls {
  track: AudioTrack;
  playing: boolean;
  volume: number;
  play: () => void;
  pause: () => void;
  toggle: () => void;
  setVolume: (v: number) => void;
  nextTrack: () => void;
  prevTrack: () => void;
}

const AudioContext = createContext<AudioControls | null>(null);

export function useAudio(): AudioControls {
  const ctx = useContext(AudioContext);
  if (!ctx) throw new Error("useAudio must be used within AudioProvider");
  return ctx;
}

export function AudioProvider({ children }: { children: ReactNode }) {
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const [state, setState] = useState<AudioState>(loadState);
  const stateRef = useRef(state);

  const track = AUDIO_TRACKS[state.trackIndex] ?? AUDIO_TRACKS[0];

  useEffect(() => {
    stateRef.current = state;
  }, [state]);

  useEffect(() => {
    const el = audioRef.current;
    if (!el) return;
    el.volume = state.volume;
  }, [state.volume]);

  const update = useCallback((patch: Partial<AudioState>) => {
    setState((prev) => {
      const next = { ...prev, ...patch };
      saveState(next);
      return next;
    });
  }, []);

  const play = useCallback(() => {
    const el = audioRef.current;
    if (!el) return;
    el.play().then(
      () => update({ playing: true }),
      () => {
        // autoplay blocked — don't update state, browser requires gesture
      }
    );
  }, [update]);

  const pause = useCallback(() => {
    audioRef.current?.pause();
    update({ playing: false });
  }, [update]);

  const toggle = useCallback(() => {
    if (stateRef.current.playing) pause();
    else play();
  }, [play, pause]);

  const setVolume = useCallback(
    (v: number) => {
      if (audioRef.current) audioRef.current.volume = v;
      update({ volume: v });
    },
    [update]
  );

  const switchTrack = useCallback(
    (index: number) => {
      update({ trackIndex: index, playing: false });
      const el = audioRef.current;
      if (el) {
        el.load();
      }
    },
    [update]
  );

  const nextTrack = useCallback(() => {
    const next = (stateRef.current.trackIndex + 1) % AUDIO_TRACKS.length;
    switchTrack(next);
  }, [switchTrack]);

  const prevTrack = useCallback(() => {
    const prev =
      (stateRef.current.trackIndex - 1 + AUDIO_TRACKS.length) %
      AUDIO_TRACKS.length;
    switchTrack(prev);
  }, [switchTrack]);

  return (
    <AudioContext.Provider
      value={{
        track,
        playing: state.playing,
        volume: state.volume,
        play,
        pause,
        toggle,
        setVolume,
        nextTrack,
        prevTrack,
      }}
    >
      {children}
      <audio ref={audioRef} src={track.url} preload="none" loop />
    </AudioContext.Provider>
  );
}
