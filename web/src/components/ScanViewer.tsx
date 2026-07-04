import { useState } from 'react';
import { AnimatePresence, motion } from 'framer-motion';
import type { BoneAgePrediction } from '../lib/api';

type Phase = 'preview' | 'analyzing' | 'result';

/**
 * Radiograph light-box: shows the loaded film, an animated scan-line while the
 * engine runs, and the returned crop bounding box overlaid in original-pixel
 * space (positioned by percentage so it scales with any display size).
 */
export function ScanViewer({
  src,
  phase,
  result,
}: {
  src: string;
  phase: Phase;
  result: BoneAgePrediction | null;
}) {
  const [nat, setNat] = useState<{ w: number; h: number } | null>(null);

  const bboxStyle =
    result && nat
      ? {
          left: `${(result.bbox[0] / nat.w) * 100}%`,
          top: `${(result.bbox[1] / nat.h) * 100}%`,
          width: `${(result.bbox[2] / nat.w) * 100}%`,
          height: `${(result.bbox[3] / nat.h) * 100}%`,
        }
      : undefined;

  return (
    <div className="viewer" data-phase={phase}>
      <div className="viewer__frame">
       <div className="viewer__film">
        <img
          className="viewer__img"
          src={src}
          alt="Loaded hand radiograph"
          onLoad={(e) =>
            setNat({
              w: e.currentTarget.naturalWidth,
              h: e.currentTarget.naturalHeight,
            })
          }
        />

        {/* Grid graticule */}
        <div className="viewer__graticule" aria-hidden />

        {/* Scan-line during analysis */}
        <AnimatePresence>
          {phase === 'analyzing' && (
            <motion.div
              key="scan"
              className="viewer__scan"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
            >
              <span className="viewer__scanline" />
            </motion.div>
          )}
        </AnimatePresence>

        {/* Crop bbox overlay */}
        <AnimatePresence>
          {phase === 'result' && bboxStyle && (
            <motion.div
              key="bbox"
              className="viewer__bbox"
              style={bboxStyle}
              initial={{ opacity: 0, scale: 1.04 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ duration: 0.5, ease: [0.16, 1, 0.3, 1] }}
            >
              <span className="viewer__bbox-tag mono">
                HAND · {Math.round((result?.crop_confidence ?? 0) * 100)}%
              </span>
            </motion.div>
          )}
        </AnimatePresence>
       </div>
      </div>
    </div>
  );
}
