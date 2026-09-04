import { useEffect, useState } from "react";

import { applyHistoryEvent, loadHistory, restoreLiveSnapshot } from "../api/history";
import type { AgentEvent } from "../models/agent";
import { useAgentStore } from "../store/agents";

const SPEEDS = [1, 2, 5] as const;

export function ReplayControls() {
  const [events, setEvents] = useState<AgentEvent[]>([]);
  const [cursor, setCursor] = useState(0);
  const [playing, setPlaying] = useState(false);
  const [speed, setSpeed] = useState<(typeof SPEEDS)[number]>(1);
  const replayMode = useAgentStore((state) => state.replayMode);

  useEffect(() => {
    if (!replayMode || !playing || cursor >= events.length) return;
    const timer = window.setTimeout(() => {
      applyHistoryEvent(events[cursor]);
      setCursor((value) => value + 1);
    }, 800 / speed);
    return () => window.clearTimeout(timer);
  }, [cursor, events, playing, replayMode, speed]);

  useEffect(() => {
    if (events.length && cursor >= events.length) setPlaying(false);
  }, [cursor, events.length]);

  const start = async () => {
    const history = await loadHistory();
    useAgentStore.getState().reset();
    useAgentStore.getState().setReplayMode(true);
    setEvents(history);
    setCursor(0);
    setPlaying(true);
  };
  const exit = async () => {
    setPlaying(false);
    useAgentStore.getState().setReplayMode(false);
    await restoreLiveSnapshot();
  };

  return (
    <div className="replay-controls">
      {!replayMode ? <button onClick={() => void start()}>Replay history</button> : (
        <>
          <button onClick={() => setPlaying((value) => !value)}>{playing ? "Pause" : "Play"}</button>
          <span>{cursor} / {events.length}</span>
          {SPEEDS.map((value) => <button className={speed === value ? "active" : ""} key={value} onClick={() => setSpeed(value)}>{value}×</button>)}
          <button onClick={() => void exit()}>Live</button>
        </>
      )}
    </div>
  );
}
