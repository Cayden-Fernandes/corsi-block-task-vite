import React, { useState } from "react";
import CandidateForm from "./CandidateForm";
import CorsiBoard from "./CorsiBoard";
import "./corsi.css";

const API_BASE = "http://localhost:8000/api";

function App() {
  const [view, setView] = useState("details"); // 'details' | 'menu' | 'task' | 'instructions' | 'db'
  const [candidate, setCandidate] = useState(null);
  const [sessionId, setSessionId] = useState(null);
  const [initialState, setInitialState] = useState(null);
  const [dbStats, setDbStats] = useState(null);

  const handleDetailsSaved = (details) => {
    setCandidate(details);
    setView("menu");
  };

  const handleStartTask = async () => {
    if (!candidate) {
      alert("Please enter candidate details first.");
      setView("details");
      return;
    }

    try {
      const res = await fetch(`${API_BASE}/start-session`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(candidate),
      });
      if (!res.ok) {
        alert("Error starting session");
        return;
      }
      const data = await res.json();
      setSessionId(data.session_id);
      setInitialState(data.state);
      setView("task");
    } catch (err) {
      console.error(err);
      alert("Network error starting session");
    }
  };

  const handleViewDb = async () => {
    try {
      const res = await fetch(`${API_BASE}/stats`);
      if (!res.ok) {
        alert("Error loading database status");
        return;
      }
      const data = await res.json();
      setDbStats(data);
      setView("db");
    } catch (err) {
      console.error(err);
      alert("Network error loading database status");
    }
  };

  const handleExit = () => {
    setCandidate(null);
    setSessionId(null);
    setInitialState(null);
    setDbStats(null);
    setView("details");
  };

  const renderMenu = () => (
    <div className="menu-container">
      {candidate && (
        <div className="candidate-summary">
          <h2>Current Candidate</h2>
          <p>Name: {candidate.candidate_name}</p>
          <p>ID: {candidate.candidate_id}</p>
          <p>Age: {candidate.age}</p>
          <p>Examiner: {candidate.examiner_name}</p>
        </div>
      )}

      <h2>COGNITIVE ASSESSMENT SUITE</h2>
      <h3>Corsi Block Tapping Task</h3>

      <div className="menu-options">
        <button onClick={handleStartTask}>Start Corsi Task</button>
        <button onClick={() => setView("details")}>Edit Candidate Details</button>
        <button onClick={handleViewDb}>View Database Status</button>
        <button onClick={() => setView("instructions")}>View Instructions</button>
        <button onClick={handleExit}>Exit</button>
      </div>

      <p className="menu-hint">Select an option above.</p>
    </div>
  );

  const renderInstructions = () => (
    <div className="text-panel">
      <h2>Instructions</h2>
      <p>
        This test measures visual-spatial working memory. Blocks will light up
        in a sequence. The candidate must reproduce the sequence by clicking
        the blocks in the same order.
      </p>
      <ul>
        <li>Blocks change their positions on each new round.</li>
        <li>When a block is clicked, it will highlight red so it is clear it was pressed.</li>
        <li>The task stops after the discontinue rule is triggered.</li>
      </ul>
      <button onClick={() => setView("menu")}>Back to Menu</button>
    </div>
  );

  const renderDbStatus = () => (
    <div className="text-panel">
      <h2>Database Status</h2>
      {!dbStats ? (
        <p>No data loaded.</p>
      ) : (
        <>
          <p>Total Candidates: {dbStats.candidate_count}</p>
          <p>Total Test Sessions: {dbStats.session_count}</p>
          <h3>Recent Sessions</h3>
          {dbStats.recent_sessions.length === 0 ? (
            <p>No sessions recorded yet.</p>
          ) : (
            <ul>
              {dbStats.recent_sessions.map((s, idx) => (
                <li key={idx}>
                  {s.candidate_name} – Session {s.session_number} – Span{" "}
                  {s.corsi_span} – {s.test_date.slice(0, 10)}
                </li>
              ))}
            </ul>
          )}
        </>
      )}
      <button onClick={() => setView("menu")}>Back to Menu</button>
    </div>
  );

  return (
    <div className="app-root">
      <h1>Corsi Block Tapping Task</h1>

      {view === "details" && (
        <CandidateForm
          initial={candidate}
          onDetailsSaved={handleDetailsSaved}
          onCancel={() => setView(candidate ? "menu" : "details")}
        />
      )}

      {view === "menu" && renderMenu()}
      {view === "instructions" && renderInstructions()}
      {view === "db" && renderDbStatus()}

      {view === "task" && sessionId && initialState && (
        <CorsiBoard
          sessionId={sessionId}
          initialState={initialState}
          onFinished={() => setView("menu")}
        />
      )}
    </div>
  );
}

export default App;
