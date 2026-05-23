theorem add_zero_example (n : Nat) : n + 0 = n := by
  simp

theorem zero_add_example (n : Nat) : 0 + n = n := by
  simp

theorem and_comm_example (p q : Prop) : p ∧ q → q ∧ p := by
  intro h
  exact And.intro h.right h.left
