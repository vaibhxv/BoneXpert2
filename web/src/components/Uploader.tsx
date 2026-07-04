import { useCallback, useRef, useState } from 'react';
import { motion } from 'framer-motion';

const ACCEPT = ['image/png', 'image/jpeg', 'image/bmp', 'image/tiff'];
const ACCEPT_ATTR = '.png,.jpg,.jpeg,.bmp,.tif,.tiff,.dcm,.dicom';

function isAllowed(file: File): boolean {
  if (ACCEPT.includes(file.type)) return true;
  // DICOM often has no/odd mime; accept by extension.
  return /\.(dcm|dicom|tif|tiff)$/i.test(file.name);
}

/** Radiograph "load film" drop zone. */
export function Uploader({
  onFile,
  disabled,
}: {
  onFile: (file: File) => void;
  disabled?: boolean;
}) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [dragging, setDragging] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handle = useCallback(
    (file: File | undefined) => {
      if (!file) return;
      if (!isAllowed(file)) {
        setError('Unsupported file. Use PNG, JPEG, TIFF, BMP or DICOM.');
        return;
      }
      setError(null);
      onFile(file);
    },
    [onFile],
  );

  return (
    <div className="uploader">
      <motion.button
        type="button"
        className="uploader__zone"
        data-dragging={dragging}
        disabled={disabled}
        whileHover={{ scale: disabled ? 1 : 1.005 }}
        whileTap={{ scale: disabled ? 1 : 0.995 }}
        onClick={() => inputRef.current?.click()}
        onDragOver={(e) => {
          e.preventDefault();
          if (!disabled) setDragging(true);
        }}
        onDragLeave={() => setDragging(false)}
        onDrop={(e) => {
          e.preventDefault();
          setDragging(false);
          if (!disabled) handle(e.dataTransfer.files?.[0]);
        }}
      >
        <span className="uploader__corner tl" aria-hidden />
        <span className="uploader__corner tr" aria-hidden />
        <span className="uploader__corner bl" aria-hidden />
        <span className="uploader__corner br" aria-hidden />

        <svg className="uploader__icon" viewBox="0 0 48 48" fill="none" aria-hidden>
          <path
            d="M24 32V12m0 0-8 8m8-8 8 8"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
          />
          <path
            d="M8 30v4a4 4 0 0 0 4 4h24a4 4 0 0 0 4-4v-4"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
          />
        </svg>

        <span className="uploader__title">Load radiograph film</span>
        <span className="uploader__hint mono">
          Drop a hand X-ray · PNG / JPEG / TIFF / DICOM
        </span>
      </motion.button>

      <input
        ref={inputRef}
        type="file"
        accept={ACCEPT_ATTR}
        hidden
        onChange={(e) => handle(e.target.files?.[0])}
      />

      {error && (
        <p className="uploader__error mono" role="alert">
          {error}
        </p>
      )}
    </div>
  );
}
