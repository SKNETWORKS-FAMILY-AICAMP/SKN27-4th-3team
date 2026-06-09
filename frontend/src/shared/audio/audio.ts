import { useEffect } from "react";

export const BGM_TRACKS = {
  menu: "/prototype/assets/배경음악/The_Nursery_s_Iron_Spring(Game Start).mp3",
  prologue: "/prototype/assets/배경음악/The_Mirror_Held_Tight(Scenario).mp3",
  turnEarly: "/prototype/assets/배경음악/Behind_the_Brick(1~4 turn).mp3",
  turnMiddle: "/prototype/assets/배경음악/Knuckles_on_the_Wood(5~8 turn).mp3",
  turnLate: "/prototype/assets/후보 트랙/The_Porcelain_Cracks.mp3",
  clear: "/prototype/assets/배경음악/First_Breath_Outside(Clear).mp3",
  gameOver: "/prototype/assets/배경음악/It_Was_Me_All_Along(Game over).mp3",
  sanityGameOver: "/prototype/assets/배경음악/The_Final_Bolt(Game over2).mp3",
} as const;

export const SFX_TRACKS = {
  journalPage: "/prototype/assets/효과음/flipping-book-page.mp3",
  ghostDeceive: "/prototype/assets/효과음/ghost-horror-sound.mp3",
  ghostCursed: "/prototype/assets/효과음/creepy-ghost-scream.mp3",
  ghostInsight: "/prototype/assets/효과음/scary-ghost-whisper.mp3",
  cardUse: "/prototype/assets/효과음/taking-playing-card.mp3",
} as const;

type MusicOptions = {
  volume?: number;
};

type SoundOptions = {
  volume?: number;
};

type MirrorGuestAudioApi = {
  playMusic: (src: string, options?: MusicOptions) => void;
  stopMusic: () => void;
  playSfx: (src: string, options?: SoundOptions) => void;
  currentMusicSrc: () => string;
};

declare global {
  interface Window {
    __mirrorGuestAudio?: MirrorGuestAudioApi;
  }
}

let musicElement: HTMLAudioElement | null = null;
let currentMusicSource = "";
let pendingPlay: HTMLAudioElement | null = null;
let unlockBound = false;

export function ensureAudioBridge(): MirrorGuestAudioApi | null {
  if (typeof window === "undefined") return null;

  if (!window.__mirrorGuestAudio) {
    window.__mirrorGuestAudio = {
      playMusic: playBackgroundMusic,
      stopMusic: stopBackgroundMusic,
      playSfx: playSoundEffect,
      currentMusicSrc: () => currentMusicSource,
    };
  }

  return window.__mirrorGuestAudio;
}

export function useBackgroundMusic(src: string | null, options: MusicOptions = {}) {
  useEffect(() => {
    ensureAudioBridge();

    if (!src) {
      stopBackgroundMusic();
      return undefined;
    }

    playBackgroundMusic(src, options);
    return undefined;
  }, [options.volume, src]);
}

export function playBackgroundMusic(src: string, { volume = 0.42 }: MusicOptions = {}) {
  if (typeof window === "undefined" || !src) return;
  ensureUnlockListener();

  const normalizedSource = normalizeAudioSource(src);
  if (musicElement && currentMusicSource === normalizedSource) {
    musicElement.volume = volume;
    attemptPlay(musicElement);
    return;
  }

  if (musicElement) {
    musicElement.pause();
    musicElement.src = "";
  }

  musicElement = new Audio(normalizedSource);
  musicElement.loop = true;
  musicElement.volume = volume;
  musicElement.preload = "auto";
  currentMusicSource = normalizedSource;
  attemptPlay(musicElement);
}

export function stopBackgroundMusic() {
  if (!musicElement) return;
  musicElement.pause();
  musicElement = null;
  currentMusicSource = "";
}

export function playSoundEffect(src: string, { volume = 0.58 }: SoundOptions = {}) {
  if (typeof window === "undefined" || !src) return;
  ensureUnlockListener();

  const effect = new Audio(normalizeAudioSource(src));
  effect.volume = volume;
  effect.preload = "auto";
  attemptPlay(effect);
}

function normalizeAudioSource(src: string) {
  return new URL(src, window.location.origin).href;
}

function attemptPlay(audio: HTMLAudioElement) {
  const playPromise = audio.play();
  if (playPromise) {
    playPromise.catch(() => {
      pendingPlay = audio;
    });
  }
}

function ensureUnlockListener() {
  if (unlockBound || typeof window === "undefined") return;
  unlockBound = true;

  const unlock = () => {
    if (pendingPlay) {
      attemptPlay(pendingPlay);
      pendingPlay = null;
    } else if (musicElement) {
      attemptPlay(musicElement);
    }
  };

  window.addEventListener("pointerdown", unlock, { passive: true });
  window.addEventListener("keydown", unlock);
}
