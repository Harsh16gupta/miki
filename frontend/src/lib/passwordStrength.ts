export interface Strength {
  score: number; // 0-4
  label: string;
}

/** T37: length + character-class scoring (mirrors server min-8 rule). */
export function passwordStrength(pw: string): Strength {
  let score = 0;
  if (pw.length >= 8) score += 1;
  if (pw.length >= 12) score += 1;
  if (/[0-9]/.test(pw) && /[a-zA-Z]/.test(pw)) score += 1;
  if (/[^a-zA-Z0-9]/.test(pw)) score += 1;
  const labels = ["Too weak", "Weak", "Okay", "Strong", "Very strong"];
  return { score, label: labels[score] };
}

export const strengthBarColors = [
  "bg-red-400",
  "bg-amber-400",
  "bg-amber-300",
  "bg-emerald-400",
  "bg-emerald-300",
];
