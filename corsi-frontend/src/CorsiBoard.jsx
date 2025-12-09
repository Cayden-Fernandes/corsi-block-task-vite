import React, { useEffect, useState } from "react";
import "./corsi.css";

const API_BASE = "https://corsi-block-task-vite.onrender.com/api";

// Generate 9 random positions (as percentages) with a minimum spacing
function generatePositions() {
  const positions = [];
  const MIN_DIST = 20; // minimum distance in "percent units"
  const minDistSq = MIN_DIST * MIN_DIST;
  let attempts = 0;

  while (positions.length < 9 && attempts < 500) {
    const x = 10 + Math.random() * 80; // 10–90%
    const y = 10 + Math.random() * 80; // 10–90%

    const ok = positions.every((p) => {
      const dx = x - p.x;
      const dy = y - p.y;
      return dx * dx + dy * dy >= minDistSq;
    });

    if (ok) {
      positions.push({ x, y });
    }
    attempts += 1;
  }

  // Fallback: simple 3×3-ish layout if random failed (very rare)
  if (positions.length < 9) {
    const fallback = [];
    const cols = [20, 50, 80];
    const rows = [20, 45, 75];
    for (let r = 0; r < 3; r++) {
      for (let c = 0; c < 3; c++) {
        fallback.push({ x: cols[c], y: rows[r] });
      }
    }
    return fallback;
  }

  return positions;
}

export default function CorsiBoard({ sessionId, initialState, onFinished }) {
  const [state, setState] = useState(initialState);
  const [sequence, setSequence] = useState([]);
  const [positions, setPositions] = useState(generatePositions()); // index = blockId
  const [activeBlockId, setActiveBlockId] = useState(null);
  const [userInput, setUserInput] = useState([]);
  const [status, setStatus] = useState("");
  const [isPlaying, setIsPlaying] = useState(false);
  const [finished, setFinished] = useState(false);
  const [summary, setSummary] = useState(null);

  // Load a new sequence AND reposition blocks
  const loadSequence = async () => {
    setStatus("Loading sequence...");
    setUserInput([]);

    try {
      const res = await fetch(`${API_BASE}/sequence/${sessionId}`);
      if (!res.ok) {
        setStatus("Error loading sequence");
        return;
      }

      const data = await res.json();

      // New random positions for this round (blocks move)
      setPositions(generatePositions());

      setSequence(data.sequence);
      setState(data.state);
      playSequence(data.sequence, data.state);
    } catch (err) {
      console.error(err);
      setStatus("Network error while loading sequence");
    }
  };

  // Playback: highlight blocks in order
  const playSequence = (seq, newState) => {
    setIsPlaying(true);
    setStatus(
      `Watch the sequence (Span: ${newState.span_length}, Trial: ${newState.trial_number})`
    );

    let i = 0;
    const interval = setInterval(() => {
      const blockId = seq[i];
      setActiveBlockId(blockId);
      setTimeout(() => setActiveBlockId(null), 350);
      i += 1;
      if (i >= seq.length) {
        clearInterval(interval);
        setTimeout(() => {
          setIsPlaying(false);
          setStatus("Now repeat the sequence. Click blocks in order.");
        }, 400);
      }
    }, 800);
  };

  // When user clicks a block
  const handleBlockClick = (blockId) => {
    if (isPlaying || finished) return;

    const nextInput = [...userInput, blockId];
    setUserInput(nextInput);

    if (nextInput.length === sequence.length) {
      submitTrial(nextInput);
    }
  };

  // Submit trial to backend
  const submitTrial = async (response) => {
    setStatus("Checking response...");

    try {
      const res = await fetch(`${API_BASE}/submit-trial`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          session_id: sessionId,
          sequence,
          response,
        }),
      });

      if (!res.ok) {
        setStatus("Error submitting trial");
        return;
      }

      const data = await res.json();
      const { trial_result, summary } = data;

      if (trial_result.correct) {
        setStatus("✓ Correct!");
      } else {
        setStatus("✗ Incorrect");
      }

      if (trial_result.finished) {
        setFinished(true);
        if (summary) {
          setSummary(summary);
          setStatus(
            `Task finished. Corsi span: ${summary.corsi_span}, Accuracy: ${summary.accuracy.toFixed(
              1
            )}%`
          );
        }
        if (onFinished) {
          setTimeout(onFinished, 1500);
        }
      } else {
        setState(trial_result.next_state);
        setTimeout(loadSequence, 1200);
      }
    } catch (err) {
      console.error(err);
      setStatus("Network error submitting trial");
    }
  };

  // First round
  useEffect(() => {
    loadSequence();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Render 9 blocks, each absolutely positioned
  const blocks = Array.from({ length: 9 }, (_, id) => id);

  return (
    <div className="corsi-container">
      <p className="status-text">{status}</p>

      <div className="corsi-area-wrapper">
        <div className="corsi-area">
          {blocks.map((blockId) => {
            const pos = positions[blockId];
            const isActive = activeBlockId === blockId;
            const isClicked = userInput.includes(blockId);

            return (
              <button
                key={blockId}
                className={[
                  "corsi-block",
                  isActive ? "corsi-block-active" : "",
                  isClicked ? "corsi-block-clicked" : "",
                ]
                  .filter(Boolean)
                  .join(" ")}
                style={{
                  left: `${pos?.x ?? 50}%`,
                  top: `${pos?.y ?? 50}%`,
                }}
                onClick={() => handleBlockClick(blockId)}
              />
            );
          })}
        </div>
      </div>

      {!finished && (
        <button
          className="control-btn"
          onClick={loadSequence}
          disabled={isPlaying}
        >
          Replay / New Sequence
        </button>
      )}

      {finished && summary && (
        <div className="summary-card">
          <h3>Session Summary</h3>
          <p>Corsi Span: {summary.corsi_span}</p>
          <p>Accuracy: {summary.accuracy.toFixed(1)}%</p>
          <p>Total Trials: {summary.total_trials}</p>
          <p>Correct Trials: {summary.correct_trials}</p>
        </div>
      )}
    </div>
  );
}
