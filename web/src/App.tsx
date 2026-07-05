import { useCallback, useEffect, useState } from 'react';
import { AnimatePresence, motion } from 'framer-motion';

import { HandSkeleton } from './components/HandSkeleton';
import { HealthBadge } from './components/HealthBadge';
import { ResultConsole } from './components/ResultConsole';
import { ScanViewer } from './components/ScanViewer';
import { SexToggle } from './components/SexToggle';
import { Uploader } from './components/Uploader';
import { predict, type BoneAgePrediction, type Sex } from './lib/api';

type Phase = 'idle' | 'ready' | 'analyzing' | 'result' | 'error';

export default function App() {
  const [file, setFile] = useState<File | null>(null);
  const [preview, setPreview] = useState<string | null>(null);
  const [sex, setSex] = useState<Sex>('female');
  const [phase, setPhase] = useState<Phase>('idle');
  const [result, setResult] = useState<BoneAgePrediction | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    return () => {
      if (preview) URL.revokeObjectURL(preview);
    };
  }, [preview]);

  const onFile = useCallback(
    (f: File) => {
      if (preview) URL.revokeObjectURL(preview);
      setFile(f);
      setPreview(URL.createObjectURL(f));
      setResult(null);
      setError(null);
      setPhase('ready');
    },
    [preview],
  );

  const analyze = useCallback(async () => {
    if (!file) return;
    setPhase('analyzing');
    setError(null);
    try {
      const res = await predict(file, sex);
      setResult(res);
      setPhase('result');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Analysis failed.');
      setPhase('error');
    }
  }, [file, sex]);

  const reset = useCallback(() => {
    if (preview) URL.revokeObjectURL(preview);
    setFile(null);
    setPreview(null);
    setResult(null);
    setError(null);
    setPhase('idle');
  }, [preview]);

  const busy = phase === 'analyzing';

  return (
    <>
      <div className="grain" aria-hidden />
      <main className="shell">
        {/* ---- Header ---- */}
        <header className="topbar">
          <a className="wordmark" href="#top">
            <span className="wordmark__glyph" aria-hidden>
              {/* small radius/ulna mark */}
              <svg viewBox="0 0 24 24" fill="none">
                <path
                  d="M8 21c0-6 2-9 4-18M16 21c0-6-2-9-4-18"
                  stroke="currentColor"
                  strokeWidth="1.6"
                  strokeLinecap="round"
                />
                <circle cx="12" cy="3.2" r="2" fill="currentColor" />
              </svg>
            </span>
            <span className="wordmark__text">
              Bone<span className="wordmark__x">X</span>pert
              <sup className="wordmark__ver mono">2.0</sup>
            </span>
          </a>
          <HealthBadge />
        </header>

        {/* ---- Stage ---- */}
        <section className="stage" id="top">
          <div className="stage__intro">
            <p className="eyebrow">Offline skeletal age · pediatric hand radiograph</p>
            <h1 className="display headline">
              Read the age
              <br />
              written in
              <span className="headline__accent"> bone.</span>
            </h1>
            <p className="lede">
              Drop a hand X-ray. The engine crops the hand, matches it to a
              reference, and estimates skeletal maturity in seconds — entirely
              on your own hardware.
            </p>

            <AnimatePresence mode="wait">
              {phase === 'idle' ? (
                <motion.div
                  key="upload"
                  initial={{ opacity: 0, y: 12 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -12 }}
                >
                  <Uploader onFile={onFile} />
                </motion.div>
              ) : (
                <motion.div
                  key="controls"
                  className="controls"
                  initial={{ opacity: 0, y: 12 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -12 }}
                >
                  <div className="controls__row">
                    <span className="eyebrow">Patient sex</span>
                    <SexToggle value={sex} onChange={setSex} disabled={busy} />
                  </div>

                  <div className="controls__actions">
                    <button
                      type="button"
                      className="btn btn--primary"
                      onClick={analyze}
                      disabled={busy}
                    >
                      {busy ? 'Analyzing…' : phase === 'result' ? 'Re-analyze' : 'Estimate bone age'}
                    </button>
                    <button
                      type="button"
                      className="btn btn--ghost"
                      onClick={reset}
                      disabled={busy}
                    >
                      New film
                    </button>
                  </div>

                  <AnimatePresence>
                    {phase === 'error' && error && (
                      <motion.div
                        className="controls__error"
                        role="alert"
                        initial={{ opacity: 0, height: 0 }}
                        animate={{ opacity: 1, height: 'auto' }}
                        exit={{ opacity: 0, height: 0 }}
                      >
                        <span aria-hidden className="controls__error-glyph">
                          ⚠
                        </span>
                        <span>{error}</span>
                      </motion.div>
                    )}
                  </AnimatePresence>
                </motion.div>
              )}
            </AnimatePresence>
          </div>

          <div className="stage__visual">
            <AnimatePresence mode="wait">
              {preview ? (
                <motion.div
                  key="viewer"
                  initial={{ opacity: 0, scale: 0.98 }}
                  animate={{ opacity: 1, scale: 1 }}
                  exit={{ opacity: 0, scale: 0.98 }}
                  transition={{ duration: 0.5, ease: [0.16, 1, 0.3, 1] }}
                >
                  <ScanViewer
                    src={preview}
                    phase={
                      phase === 'analyzing'
                        ? 'analyzing'
                        : phase === 'result'
                          ? 'result'
                          : 'preview'
                    }
                    result={result}
                  />
                </motion.div>
              ) : (
                <motion.div
                  key="hand"
                  className="hero-hand-wrap"
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  exit={{ opacity: 0 }}
                >
                  <HandSkeleton className="hero-hand" />
                  <div className="hero-hand__caption eyebrow">Fig. 01 — carpal atlas</div>
                </motion.div>
              )}
            </AnimatePresence>
          </div>
        </section>

        {/* ---- Result ---- */}
        <AnimatePresence>
          {phase === 'result' && result && (
            <motion.section
              className="result"
              initial={{ opacity: 0, y: 24 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0 }}
              transition={{ duration: 0.6, ease: [0.16, 1, 0.3, 1] }}
            >
              <ResultConsole result={result} />
            </motion.section>
          )}
        </AnimatePresence>

        {/* ---- Footer ---- */}
        <footer className="footer">
          <div className="footer__pipeline mono">
            <span>upload</span>
            <span className="footer__arrow">→</span>
            <span>crop</span>
            <span className="footer__arrow">→</span>
            <span>hist-match</span>
            <span className="footer__arrow">→</span>
            <span>estimate</span>
          </div>
          <p className="footer__disclaimer">
            Research &amp; demonstration only. Not a medical device and not
            approved for clinical use.
          </p>
        </footer>
      </main>
    </>
  );
}
