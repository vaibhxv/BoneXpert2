import { motion } from 'framer-motion';

/**
 * Hand-drawn anatomical hand-skeleton line art (no external asset).
 * Bones are rendered as capsule strokes with joint nodes; the whole hand
 * "draws on" via animated pathLength for a radiographic reveal.
 */

type Pt = [number, number];

// Each finger = ordered joint points from base -> tip (in viewBox coords).
const FINGERS: Pt[][] = [
  // Thumb (angled, 2 phalanges + metacarpal)
  [
    [150, 372],
    [104, 340],
    [74, 296],
    [52, 258],
    [36, 226],
  ],
  // Index
  [
    [150, 372],
    [120, 300],
    [115, 236],
    [110, 178],
    [106, 128],
  ],
  // Middle
  [
    [150, 372],
    [150, 296],
    [150, 224],
    [150, 158],
    [150, 100],
  ],
  // Ring
  [
    [150, 372],
    [180, 300],
    [186, 238],
    [192, 180],
    [197, 132],
  ],
  // Pinky
  [
    [150, 372],
    [206, 308],
    [216, 258],
    [224, 214],
    [230, 178],
  ],
];

// Collect unique joint nodes (skip the shared wrist hub duplication).
const JOINTS: Pt[] = [
  [150, 372],
  ...FINGERS.flatMap((f) => f.slice(1)),
];

function polyPath(points: Pt[]): string {
  return points
    .map((p, i) => `${i === 0 ? 'M' : 'L'} ${p[0]} ${p[1]}`)
    .join(' ');
}

const container = {
  hidden: {},
  show: { transition: { staggerChildren: 0.05, delayChildren: 0.15 } },
};

const boneVariant = {
  hidden: { pathLength: 0, opacity: 0 },
  show: {
    pathLength: 1,
    opacity: 1,
    transition: { pathLength: { duration: 1.1, ease: [0.16, 1, 0.3, 1] } },
  },
};

const jointVariant = {
  hidden: { scale: 0, opacity: 0 },
  show: { scale: 1, opacity: 1, transition: { duration: 0.4, ease: 'backOut' } },
};

export function HandSkeleton({ className }: { className?: string }) {
  return (
    <motion.svg
      className={className}
      viewBox="0 0 300 440"
      fill="none"
      role="img"
      aria-label="Anatomical hand skeleton"
      variants={container}
      initial="hidden"
      animate="show"
    >
      <defs>
        <linearGradient id="boneGrad" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor="#f4ecd9" />
          <stop offset="100%" stopColor="#b7ae9c" />
        </linearGradient>
        <filter id="boneGlow" x="-30%" y="-30%" width="160%" height="160%">
          <feGaussianBlur stdDeviation="2.4" result="b" />
          <feMerge>
            <feMergeNode in="b" />
            <feMergeNode in="SourceGraphic" />
          </feMerge>
        </filter>
      </defs>

      {/* Forearm / wrist stub */}
      <motion.path
        d="M132 372 L128 432 M168 372 L172 432"
        stroke="url(#boneGrad)"
        strokeWidth={9}
        strokeLinecap="round"
        variants={boneVariant}
        opacity={0.55}
      />

      {/* Carpal cluster */}
      <g filter="url(#boneGlow)">
        {[
          [140, 384],
          [158, 386],
          [150, 398],
          [136, 400],
          [164, 400],
        ].map(([cx, cy], i) => (
          <motion.circle
            key={`carpal-${i}`}
            cx={cx}
            cy={cy}
            r={5.4}
            fill="url(#boneGrad)"
            variants={jointVariant}
            opacity={0.75}
          />
        ))}
      </g>

      {/* Bones */}
      <g filter="url(#boneGlow)" strokeLinecap="round">
        {FINGERS.map((finger, fi) => (
          <motion.path
            key={`finger-${fi}`}
            d={polyPath(finger)}
            stroke="url(#boneGrad)"
            strokeWidth={fi === 0 ? 8.5 : 7.5 - fi * 0.4}
            variants={boneVariant}
          />
        ))}
      </g>

      {/* Joint nodes */}
      <g filter="url(#boneGlow)">
        {JOINTS.map(([cx, cy], i) => (
          <motion.circle
            key={`joint-${i}`}
            cx={cx}
            cy={cy}
            r={3.6}
            fill="#0a0a0c"
            stroke="url(#boneGrad)"
            strokeWidth={2.2}
            variants={jointVariant}
          />
        ))}
      </g>
    </motion.svg>
  );
}
