import { motion } from 'framer-motion';
import type { Sex } from '../lib/api';

const OPTIONS: { value: Sex; label: string; glyph: string }[] = [
  { value: 'female', label: 'Female', glyph: '\u2640' },
  { value: 'male', label: 'Male', glyph: '\u2642' },
];

/**
 * Segmented sex selector. Patient sex materially affects the prediction, so it
 * is a required, prominent control with a sliding phosphor indicator.
 */
export function SexToggle({
  value,
  onChange,
  disabled,
}: {
  value: Sex;
  onChange: (s: Sex) => void;
  disabled?: boolean;
}) {
  return (
    <div className="sex-toggle" role="radiogroup" aria-label="Patient sex" data-disabled={disabled}>
      {OPTIONS.map((opt) => {
        const active = value === opt.value;
        return (
          <button
            key={opt.value}
            type="button"
            role="radio"
            aria-checked={active}
            disabled={disabled}
            className="sex-toggle__opt"
            data-active={active}
            onClick={() => onChange(opt.value)}
          >
            {active && (
              <motion.span
                layoutId="sex-indicator"
                className="sex-toggle__pill"
                transition={{ type: 'spring', stiffness: 420, damping: 34 }}
              />
            )}
            <span className="sex-toggle__glyph" aria-hidden>
              {opt.glyph}
            </span>
            <span className="sex-toggle__label">{opt.label}</span>
          </button>
        );
      })}
    </div>
  );
}
