import { motion } from 'framer-motion';
import type { BoneAgePrediction } from '../lib/api';
import { CountUp } from './CountUp';

const stagger = {
  hidden: {},
  show: { transition: { staggerChildren: 0.08, delayChildren: 0.1 } },
};
const item = {
  hidden: { y: 14, opacity: 0 },
  show: { y: 0, opacity: 1, transition: { duration: 0.6, ease: [0.16, 1, 0.3, 1] } },
};

function fmtYears(years: number): { whole: number; months: number } {
  const whole = Math.floor(years);
  const months = Math.round((years - whole) * 12);
  return { whole, months };
}

export function ResultConsole({ result }: { result: BoneAgePrediction }) {
  const { whole, months } = fmtYears(result.bone_age_years);
  const confidencePct = Math.round(result.crop_confidence * 100);

  return (
    <motion.section
      className="console"
      variants={stagger}
      initial="hidden"
      animate="show"
      aria-live="polite"
    >
      <motion.div className="console__eyebrow eyebrow" variants={item}>
        Estimated skeletal age
      </motion.div>

      <motion.div className="console__headline" variants={item}>
        <span className="console__big display">
          <CountUp value={whole} />
        </span>
        <div className="console__unit">
          <span className="mono">yrs</span>
          <span className="console__submonths mono">
            {whole > 0 || months > 0 ? `${months} mo` : ''}
          </span>
        </div>
      </motion.div>

      <motion.div className="console__months mono" variants={item}>
        <CountUp value={result.bone_age_months} decimals={1} /> months total
      </motion.div>

      <motion.div className="console__meter" variants={item}>
        <div className="console__meter-head">
          <span className="eyebrow">Crop confidence</span>
          <span className="mono">{confidencePct}%</span>
        </div>
        <div className="console__meter-track">
          <motion.span
            className="console__meter-fill"
            initial={{ width: 0 }}
            animate={{ width: `${confidencePct}%` }}
            transition={{ duration: 1, ease: [0.16, 1, 0.3, 1], delay: 0.3 }}
          />
        </div>
      </motion.div>

      <motion.dl className="console__grid" variants={item}>
        <div>
          <dt className="eyebrow">Patient</dt>
          <dd className="mono">{result.sex}</dd>
        </div>
        <div>
          <dt className="eyebrow">Latency</dt>
          <dd className="mono">{result.processing_time_ms} ms</dd>
        </div>
        <div>
          <dt className="eyebrow">Model</dt>
          <dd className="mono">{result.model_version}</dd>
        </div>
        <div>
          <dt className="eyebrow">Trace</dt>
          <dd className="mono">{result.request_id}</dd>
        </div>
      </motion.dl>

      <motion.p className="console__engine mono" variants={item}>
        {result.crop_model} → {result.model}
      </motion.p>
    </motion.section>
  );
}
