import React, { useState, useEffect } from "react";

export default function CandidateForm({ initial, onDetailsSaved, onCancel }) {
  const [form, setForm] = useState({
    examiner_name: "",
    candidate_name: "",
    candidate_id: "",
    age: "",
    gender: "Male",
    session: 1,
    additional_notes: "",
  });

  useEffect(() => {
    if (initial) {
      setForm((prev) => ({
        ...prev,
        ...initial,
      }));
    }
  }, [initial]);

  const handleChange = (e) => {
    const { name, value } = e.target;
    setForm((prev) => ({ ...prev, [name]: value }));
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!form.candidate_name || !form.candidate_id) {
      alert("Candidate name and ID are required.");
      return;
    }
    onDetailsSaved({
      ...form,
      session: Number(form.session || 1),
    });
  };

  return (
    <form className="candidate-form" onSubmit={handleSubmit}>
      <h2>Candidate Details – Examiner Input</h2>

      <label>
        Examiner Name
        <input
          name="examiner_name"
          value={form.examiner_name}
          onChange={handleChange}
        />
      </label>

      <label>
        Candidate Name
        <input
          name="candidate_name"
          value={form.candidate_name}
          onChange={handleChange}
          required
        />
      </label>

      <label>
        Candidate ID
        <input
          name="candidate_id"
          value={form.candidate_id}
          onChange={handleChange}
          required
        />
      </label>

      <label>
        Age
        <input name="age" value={form.age} onChange={handleChange} />
      </label>

      <label>
        Gender
        <select name="gender" value={form.gender} onChange={handleChange}>
          <option value="Male">Male</option>
          <option value="Female">Female</option>
          <option value="Other">Other</option>
          <option value="Prefer not to say">Prefer not to say</option>
        </select>
      </label>

      <label>
        Session
        <input
          name="session"
          type="number"
          min="1"
          value={form.session}
          onChange={handleChange}
        />
      </label>

      <label>
        Additional Notes
        <input
          name="additional_notes"
          value={form.additional_notes}
          onChange={handleChange}
        />
      </label>

      <div className="form-buttons">
        <button type="submit">OK</button>
        {onCancel && (
          <button type="button" onClick={onCancel}>
            Cancel
          </button>
        )}
      </div>
    </form>
  );
}
